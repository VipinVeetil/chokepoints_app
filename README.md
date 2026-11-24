# Macroeconomic Risks from Maritime Trade Disruptions

**Vipin P. Veetil · Fathimath S. Vemmarath**

📄 **Paper:** [Macroeconomic Risks from Maritime Trade Disruptions](https://arxiv.org/abs/2607.09951) · [arXiv:2607.09951](https://arxiv.org/abs/2607.09951)

An interactive Streamlit companion to the paper *[Macroeconomic Risks from
Maritime Trade Disruptions](https://arxiv.org/abs/2607.09951)*. Close any set of the world's 12 major shipping
chokepoints, pick a `(τ, ρ, ϱ, δ)` calibration, and solve the short-run
production-network model forward — then explore where the GDP loss falls
on a world choropleth, by country, and by sector.

Every solve prices a **complete closure sustained for a year**, crediting no
overland bypass. Only the seaborne part of each trade flow is exposed to a
closure; trade that moves by pipeline, road, rail, or air stays at its
benchmark value. Eleven of the twelve gates are counterfactual; the Strait of
Hormuz has been shut since 28 February 2026.

The model and its benchmark data are the published
[`maritime-choke`](https://pypi.org/project/maritime-choke/) package; this repo
is only the Streamlit UI.

## Live app

Deployed on Streamlit Community Cloud at
[maritime-chokepoints.streamlit.app](https://maritime-chokepoints.streamlit.app).

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

On first launch the app downloads the ~90 MB benchmark cache from Zenodo
(DOI [10.5281/zenodo.21263266](https://doi.org/10.5281/zenodo.21263266)) into a
per-user data directory, then reuses it for every solve. To point at a local
cache instead, set `MARITIME_CHOKE_DATA` to a folder containing
`model_cache_2019/`.

## Deploy your own on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. **New app** → pick this repo, branch `main`, main file `streamlit_app.py`.
4. Deploy. The first boot installs the requirements and downloads the cache, so
   it takes a couple of minutes; subsequent solves are fast.

## Notes

- A single-chokepoint solve takes ~20–40 s; joint scenarios take longer and use
  more memory. On Streamlit's free tier, very large joint closures may approach
  the resource limit.
- The baseline calibration is `(τ, ρ, ϱ) = (0.3, −1, −1)` with a uniform closure
  residual transit share `δ = 0.10` applied to every seaborne sector. The paper's calibration
  rectangle runs over `τ ∈ [0.2, 0.5]` and `ρ ∈ [−1, −0.25]` with `ϱ` held at
  `−1`; `δ ∈ [0.05, 0.15]` for boxed cargo and `[0.40, 0.55]` for energy under
  attack. Note `ρ`'s effective country-sector range is `[−1, −0.25]`, not the raw
  macro-literature band `[−4, −1]`, which Online Appendix B corrects upward for
  aggregation.
- A closing harsh-corner audit releases `ϱ` and moves all four parameters at once
  to `(0.5, −4, −4, 0.01)`, where the Hormuz loss reaches 7.91%. Those cells were
  solved with damping 0.25 and tolerance 1e−10; the app exposes neither, so
  deep-curvature results will not match the paper exactly.
- The commodity-differentiated reading (`δ = 0.45` on the energy sectors
  B05/B06/C19) remains an optional toggle, but it is a robustness exercise only:
  the 2026 Hormuz closure severed energy *more* completely than other cargo, so
  the differentiation is not supported at that gate.
- Hormuz is the one gate with a solved overland bypass. The app reports the
  uncredited reading (≈2.83% of world GDP at the baseline). Crediting the Saudi
  East–West and Emirati Habshan–Fujairah pipelines at the throughput the 2026
  closure mobilized halves that (≈1.42%); day-weighting the measured 2026
  severance path gives 1.44% uncredited / 0.73% credited. Neither is reachable
  from the app's controls — see Online Appendix B, `app:hormuz_pipeline`.

## Licence

MIT (this UI code). The calibrated model inputs the app downloads from Zenodo
(DOI [10.5281/zenodo.21263266](https://doi.org/10.5281/zenodo.21263266)) are
CC BY 4.0. The proprietary primary sources they derive from (GTAP 10, OECD ICIO)
are not redistributed and carry their own terms.
