"""
streamlit_app.py — Maritime chokepoint disruption, on Streamlit.

A native Streamlit front end for the short-run production-network model of
maritime-chokepoint closures. Close any set of the 12 major shipping
chokepoints, pick a (tau, rho, varrho, delta) calibration, and the model is
solved forward; the world GDP loss is shown on a choropleth, by
country, and by sector.

Companion to the paper "Macroeconomic Risks from Maritime Trade Disruptions"
(Veetil & Vemmarath), https://arxiv.org/abs/2607.09951.

The model and its data are the published `maritime-choke` package
(https://pypi.org/project/maritime-choke/): on first launch it downloads the
~90 MB benchmark cache from Zenodo (DOI 10.5281/zenodo.21263267), then every
solve reuses it in memory. This file only builds the UI — all the compute lives
in `maritime_choke.solver_backend`.
"""
from __future__ import annotations

import json
import importlib.resources as ir
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

from maritime_choke import solver_backend as sb
from maritime_choke import data as mc_data

st.set_page_config(
    page_title="Macroeconomic Risks from Maritime Trade Disruptions",
    page_icon="🚢",
    layout="wide",
)


# --------------------------------------------------------------------------- #
# Data + metadata (fetched once per container, cached across reruns)           #
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def bootstrap():
    """Ensure the model cache is installed, then return the static UI metadata."""
    if not sb.list_caches():
        mc_data.fetch()  # downloads the benchmark cache from Zenodo (~90 MB)
    return {
        "caches": sb.list_caches(),
        "chokepoints": sb.chokepoint_labels(),
        "presets": sb.PRESETS,
        "mapmeta": sb.map_metadata(),
        "anchors": _load_anchors(),
        "sector_names": sb.SECTOR_NAMES,
    }


def _load_anchors() -> list[dict]:
    """"Scale of the loss" anchors shipped inside the maritime_choke package."""
    try:
        p = ir.files("maritime_choke") / "static" / "loss_anchors.json"
        return json.loads(p.read_text())
    except Exception:  # noqa: BLE001 — the caption is a nicety, never fatal
        return []


def scale_phrase(total_usd_m: float, anchors: list[dict]) -> str | None:
    if not anchors:
        return None
    usd_bn = total_usd_m / 1_000.0
    a = min(anchors, key=lambda x: abs(x["usd_billion"] - usd_bn))
    return f"≈ {a['phrase']} ({a['note']})"


# --------------------------------------------------------------------------- #
# Helpers to turn a solved scenario into map-ready per-ISO3 values             #
# --------------------------------------------------------------------------- #
def expand_to_iso(econ_values: dict, mapmeta: dict) -> pd.DataFrame:
    """Spread a per-economy value onto ISO-3 territories, painting the seven
    OECD-ICIO ROW aggregates onto each of their member countries."""
    row_blocks = mapmeta["row_blocks"]
    other = mapmeta["other_labels"]
    recs = []
    for econ, val in econ_values.items():
        if econ in row_blocks:
            for iso in row_blocks[econ]:
                recs.append({"iso": iso, "value": val, "name": other.get(econ, econ)})
        else:
            recs.append({"iso": econ, "value": val, "name": econ})
    return pd.DataFrame(recs)


def choropleth(df: pd.DataFrame, title: str):
    fig = px.choropleth(
        df,
        locations="iso",
        locationmode="ISO-3",
        color="value",
        hover_name="name",
        color_continuous_scale="Reds",
        range_color=(0, max(df["value"].max(), 1e-6)),
        labels={"value": "GDP loss (%)"},
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        title=dict(text=title, x=0.01, font=dict(size=14)),
        coloraxis_colorbar=dict(title="% loss"),
        geo=dict(showframe=False, showcoastlines=False, projection_type="natural earth"),
        height=430,
    )
    return fig


# --------------------------------------------------------------------------- #
# UI                                                                           #
# --------------------------------------------------------------------------- #
st.title("🚢 Macroeconomic Risks from Maritime Trade Disruptions")
st.markdown("##### Vipin P. Veetil · Fathimath S. Vemmarath")
st.caption(
    "An interactive companion to [the paper](https://arxiv.org/abs/2607.09951) — "
    "close any set of the 12 major shipping chokepoints, pick a (τ, ρ, ϱ, δ) "
    "calibration, and solve the short-run production-network model forward. "
    "Every solve prices a **complete closure sustained for a year**, crediting no "
    "overland bypass. Eleven of the twelve gates are counterfactual; the Strait of "
    "Hormuz has been shut since 28 February 2026. "
    "Model & data: the "
    "[`maritime-choke`](https://pypi.org/project/maritime-choke/) package."
)

with st.spinner("Preparing the model cache (first load downloads ~90 MB from Zenodo)…"):
    B = bootstrap()

CHOKES = B["chokepoints"]
NICE = {c["index"]: c["nice"] for c in CHOKES}
LABEL_TO_IDX = {c["nice"]: c["index"] for c in CHOKES}

# ---- Sidebar: scenario + calibration ----
if "chosen" not in st.session_state:
    st.session_state["chosen"] = []


def _apply_preset():
    """Picking a named scenario prefills the multiselect (which is keyed, so its
    state persists and can still be edited by hand afterwards)."""
    sel = st.session_state["preset_sel"]
    if sel != "— none —":
        k = sel.split(" · ")[0]
        st.session_state["chosen"] = [NICE[i] for i in B["presets"][k]["Q"]]


with st.sidebar:
    st.header("1 · Chokepoints")
    st.selectbox(
        "Named joint scenario",
        ["— none —"] + [f"{k} · {v['label']}" for k, v in B["presets"].items()],
        key="preset_sel", on_change=_apply_preset,
        help="Pick a preset to prefill the closure set, or choose chokepoints below.",
    )
    chosen = st.multiselect(
        "Chokepoints to close",
        options=[c["nice"] for c in CHOKES],
        key="chosen",
    )
    Q = sorted(LABEL_TO_IDX[l] for l in chosen)

    st.header("2 · Calibration")
    c1, c2 = st.columns(2)
    tau = c1.number_input("τ · friction", 0.0, 1.0, 0.30, 0.05,
                          help="Reallocation friction on displaced trade. "
                               "Evidence-supported range [0.30, 0.40], centre ≈0.35.")
    rho = c2.number_input("ρ · inner CES", -4.0, -0.05, -1.0, 0.05,
                          help="Curvature across the sectoral input bundle. The paper's "
                               "effective short-run country-sector range is [−1, −0.25] — the "
                               "raw macro-literature band [−4, −1] is corrected upward for the "
                               "two aggregations. Values below −1 belong to the harsh-corner audit.")
    varrho = c1.number_input("ϱ · outer CES", -4.0, -0.05, -1.0, 0.05,
                             help="Curvature between value added and the intermediate composite. "
                                  "Held at −1 throughout the paper's rectangle exercises; released "
                                  "only at the harsh corner, whose documented range is [−4, −1].")
    st.caption(
        "Baseline (τ, ρ, ϱ, δ) = (0.3, −1, −1, 0.10). The paper's **calibration "
        "rectangle** sweeps τ ∈ {0.2, 0.4, 0.5} and ρ ∈ [−1, −0.25] with ϱ held at "
        "−1; δ ∈ [0.05, 0.15] for boxed cargo, [0.40, 0.55] for energy under attack. "
        "A closing **harsh-corner audit** releases ϱ and moves all four at once to "
        "(0.5, −4, −4, 0.01), where Hormuz reaches 9.70%. Those deep-curvature cells "
        "were solved with damping 0.25 and tolerance 1e−10, neither of which this app "
        "exposes, so results near the corner will not match the paper exactly."
    )

    energy = st.toggle("Energy-specific leakage (δ on B05/B06/C19)", value=False)
    st.caption(
        "Robustness reading only; the baseline applies one δ to every seaborne "
        "sector. Note the 2026 Hormuz closure severed energy *more* completely "
        "than other cargo, so this differentiation is not supported at that gate."
    )
    d1, d2 = st.columns(2)
    base_delta = d1.number_input("δ base", 0.01, 0.99, 0.10, 0.05,
                                 help="Residual share a closed link keeps. Applies to every "
                                      "seaborne sector unless the energy toggle is on, in which "
                                      "case it applies outside B05/B06/C19.")
    energy_delta = d2.number_input("δ energy", 0.01, 0.99, 0.45, 0.05, disabled=not energy,
                                   help="Residual share kept on B05/B06/C19 when the toggle is on.")

    with st.expander("Advanced"):
        cache = st.selectbox("Model cache", B["caches"])
        max_outer = st.number_input("Max outer iters", 50, 2000, 500, 50)

    run = st.button("Run scenario", type="primary", width="stretch",
                    disabled=not Q)
    if not Q:
        st.info("Select at least one chokepoint.")

# ---- Solve on click; keep the result in session so recolouring doesn't resolve ----
if run:
    cfg = dict(
        Q=Q, tau=tau, rho=rho, varrho=varrho,
        base_delta=base_delta,
        energy_delta=(energy_delta if energy else None),
        cache=cache, max_outer=int(max_outer),
    )
    try:
        with st.status("Solving the coupled fixed point…", expanded=False) as status:
            summary = sb.run_scenario(cfg)
            sector = json.loads(Path(summary["outdir"], "sector_matrix.json").read_text())
            status.update(label="Done", state="complete")
        st.session_state["result"] = {"summary": summary, "sector": sector}
    except Exception as e:  # noqa: BLE001
        st.error(f"Solve failed: {e}")

# ---- Results ----
res = st.session_state.get("result")
if not res:
    st.info("Set up a scenario in the sidebar and press **Run scenario**.")
    st.stop()

summary, sector = res["summary"], res["sector"]
p = summary["params"]
solver = summary["solver"]
mapmeta = B["mapmeta"]

closed = ", ".join(summary["closed_chokepoints"]) or "—"
dtxt = f"{p['base_delta']} (energy {p['energy_delta']})" if p.get("energy_specific") else p["base_delta"]
st.markdown(
    f"**Closed:** {closed}  ·  τ={p['tau']}, ρ={p['rho']}, ϱ={p.get('varrho', -1)}, δ={dtxt}  "
    f"·  cache `{summary['cache']}`"
)

m1, m2 = st.columns([1, 2])
m1.metric("World GDP loss", f"{summary['world_lambda_pct']:.2f}%", help="Share of world GDP.")
phrase = scale_phrase(summary["total_VA_loss_USDm"], B["anchors"])
if phrase:
    m2.markdown(f"### Scale of the loss\n{phrase}")

# Hormuz is the one gate with a solved overland bypass. The paper reports both
# readings; this app solves only the uncredited one, so say which is on screen.
if 0 in summary.get("closed_indices", []):
    st.caption(
        "This Hormuz solve credits **no** overland bypass. Online Appendix B "
        "(*app:hormuz_pipeline*) re-origins Saudi and Emirati crude onto the "
        "East–West and Habshan–Fujairah pipelines at the throughput the 2026 "
        "closure actually mobilized (share φ = 0.238 of the two economies' crude "
        "sales at the gate), which roughly halves the world figure — 1.61% → 0.72% "
        "at the baseline calibration — and every Gulf country loss with it. "
        "Day-weighting the measured 2026 severance path instead of a full year "
        "gives 0.77% uncredited and 0.34% credited. Neither reading is reachable "
        "from the controls above."
    )

# ---- Map: colour by total or by a single sector ----
st.subheader("Where the GDP loss falls")
sectors = sector["sectors"]
colour_opts = ["Total GDP loss"] + [B["sector_names"].get(s, s) for s in sectors]
choice = st.selectbox("Colour by", colour_opts)

if choice == "Total GDP loss":
    econ_vals = {c["country"]: c["lambda_pct"] for c in summary["countries"]}
    title = "Total GDP loss (%)"
else:
    s_idx = colour_opts.index(choice) - 1
    econ_vals = {e: sector["loss_pct"][i][s_idx] for i, e in enumerate(sector["economies"])}
    title = f"{choice} — output lost (%)"

df = expand_to_iso(econ_vals, mapmeta)
st.plotly_chart(choropleth(df, title))

# ---- Most-exposed economies + sector drill-down ----
left, right = st.columns(2)
with left:
    st.subheader("Most-exposed economies")
    tbl = pd.DataFrame(summary["top_countries"])[["name", "lambda_pct", "phi_pct", "L_VA_USDm"]]
    tbl.columns = ["Economy", "GDP loss λ (%)", "Gross loss φ (%)", "GDP loss (USD m)"]
    st.dataframe(tbl, hide_index=True, width="stretch", height=430)

with right:
    st.subheader("A country's hardest-hit sectors")
    econs = sector["economies"]
    labels = [B["mapmeta"]["other_labels"].get(e, e) for e in econs]
    pick = st.selectbox("Economy", labels, index=labels.index(
        B["mapmeta"]["other_labels"].get("ARE", "ARE")) if "ARE" in econs else 0)
    ei = labels.index(pick)
    row = sector["loss_pct"][ei]
    sdf = pd.DataFrame({
        "Sector": [B["sector_names"].get(s, s) for s in sectors],
        "Output lost (%)": row,
    }).sort_values("Output lost (%)", ascending=False).head(12)
    st.dataframe(sdf, hide_index=True, width="stretch", height=430)

# ---- Solver diagnostics ----
diag = (
    f"Solver: {'converged' if solver['converged'] else 'stopped at cap'} in "
    f"{solver['n_iter']} outer iterations · residual {solver['residual']:.1e} · "
    f"runtime {summary['runtime_sec']}s"
)
if solver.get("cushion_violations", 0) > 0:
    diag += f" · ex-ante cushion violations: {solver['cushion_violations']} (min h {solver['min_h']:.2f})"
st.caption(diag)
