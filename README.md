# Maritime chokepoint disruption — Streamlit app

An interactive Streamlit front end for the short-run production-network model of
**maritime-chokepoint trade disruptions**. Close any set of the world's 12 major
shipping chokepoints, pick a `(τ, ρ, ϱ, δ)` calibration, and solve the model
forward — then explore where the value-added loss falls on a world choropleth,
by country, and by sector.

Based on *Macroeconomic Risks from Maritime Trade Disruptions* (Vemmarath &
Veetil). The model and its benchmark data are the published
[`maritime-choke`](https://pypi.org/project/maritime-choke/) package; this repo
is only the Streamlit UI.

## Live app

Deployed on Streamlit Community Cloud — see the link at the top of this repo.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

On first launch the app downloads the ~90 MB benchmark cache from Zenodo
(DOI [10.5281/zenodo.21263267](https://doi.org/10.5281/zenodo.21263267)) into a
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
  leakage `δ = 0.10`; the commodity-differentiated reading (`δ = 0.45` on the
  energy sectors B05/B06/C19) is an optional toggle.

## Licence

MIT (this UI code). The underlying model data (GTAP, OECD ICIO) is governed by
its own terms; see the `maritime-choke` package.
