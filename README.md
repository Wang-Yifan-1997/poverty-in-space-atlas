# Poverty in Space — Atlas

A static web atlas of **building-based predictions** of wealth, poverty and inequality at
**~5 km resolution across 52 countries** (Africa + Bangladesh), from **Google Open Buildings**
footprints alone. Every map shows the country border (ADM0).

Each location is a resolution-7 H3 hexagon (~5 km). Seven building-footprint features per hexagon
(density, built-up fraction, mean & spread of footprint size, small/medium/large size shares) feed
**buildings-only gradient-boosted models** trained on 7,442 DHS survey clusters across 12 African
countries.

## Indicators (7 predicted + 2 building-density layers)

| Indicator | Type | Definition | CV score |
|---|---|---|---|
| Wealth | continuous | median IWI (0–100) | R² 0.60 |
| Poverty rate | continuous | % households IWI < 35 | R² 0.57 |
| Extreme poverty | continuous | % households IWI < 20 | R² 0.29 |
| Inequality (CV) | continuous | within-hex CV of IWI | R² 0.42 |
| Gini | continuous | within-hex Gini of IWI | R² 0.41 |
| Poor (yes/no) | dummy | 1 if median IWI < 35, else 0 | acc 0.81 |
| High inequality (yes/no) | dummy | 1 if CV > 0.40, else 0 | acc 0.82 |
| Building density | data layer | buildings / km² (log, scale shared across countries) | — |
| Density decile | data layer | within-country building-density rank 1–10 | — |

The last two are **the raw building input, not model predictions** — reference layers so you can see the
footprint density (and its within-country rank) behind every wealth map. They exist for all three datasets.

The last two are **hard yes/no dummies (class 0/1)** — the model predicts *poor / not-poor* and
*high-inequality / not*, not a probability. They render as two-colour maps (grey = no, colour = yes).

**Coverage toggle:** *Screened* = hexes with ≥10 buildings (the model's training floor, where
footprint-shape features are stable); *All buildings* = every populated hex (noisier). Colours use one
fixed scale per indicator across all countries.

**Period selector.** The default view is the static **v3** atlas (2023, Google v3, 52 countries). A
**Period** control also offers **2016** and **2023** from the **Google Open Buildings 2.5D temporal
panel** for 12 countries with a building time series (BFA, BGD, CIV, CMR, GHA, GIN, KEN, LSO, MDG, MOZ,
MWI, SEN). The 2.5D product has no footprint-size features, so those models are retrained on count /
density / built-up fraction / building height and are slightly less accurate (wealth R²=0.50 vs 0.60);
scales are fixed across both years so 2016 vs 2023 is directly comparable.

Predictions are model estimates, not official statistics — most reliable in Sub-Saharan Africa; North
Africa and small islands are extrapolations; extreme poverty (a rare tail) is the least accurate.

## Live site

**https://Wang-Yifan-1997.github.io/poverty-in-space-atlas/**

## Repository layout

Pages: **Atlas** (`index.html`, the maps) · **Descriptives** (`descriptives.html`, per-country
distributions & persistence explorer) · **Over time** (`dynamics.html`, narrative essay).

```
index.html                                  # atlas — the maps (no build step)
descriptives.html                           # per-country distributions & persistence explorer
dynamics.html                               # "Over time" narrative essay
assets/{style.css, app.js, manifest.js}     # manifest.js = window.ATLAS (generated)
assets/{descriptives_app.js, descriptives_manifest.js}   # the descriptives explorer
figures/
  full/{screening}/{outcome}/{ISO}.png      # titled + colourbar (lightbox)
  thumb/{screening}/{outcome}/{ISO}.png     # clean thumbnails (grid)
  temporal/{full,thumb}/{screening}/{year}/{outcome}/{ISO}.png  # 2.5D 2016 & 2023 panel
data/countries.json                         # manifest: outcomes, screenings, per-country stats
figures/descriptives/{tab}/{dataset}/{ISO}.png  # descriptives figs (tab: density|wealth|spatial; +temporal/{ISO}.png)
scripts/build_maps.py                       # regenerates every atlas figure + manifest
scripts/make_descriptives.py                # regenerates the descriptives figures + manifest
```

`{screening}` ∈ `screened`, `all`. `{outcome}` ∈ `wealth`, `poverty_rate`, `extreme_rate`,
`inequality_cv`, `gini`, `poverty_dummy`, `inequality_dummy`, `bld_density`, `bld_decile`.
`{ISO}` = ISO 3166-1 alpha-3. The two `bld_*` layers are added by `scripts/make_density_layers.py`.

## View locally

```bash
python -m http.server 5173   # then open http://localhost:5173
```

## Regenerate

The rendered PNGs are committed. To rebuild from the prediction table (research repo):

```bash
python scripts/build_maps.py            # all countries
python scripts/build_maps.py KEN NGA    # quick test on a subset
```

Model pipeline (research repo, `task8_demand_trap`): `extract_labels_extra.py` (DHS labels) →
`train_all_outcomes.py` (7 models) → `predict_all_outcomes.py` → `build_maps.py`. The 2016/2023 temporal
panel is incorporated separately by `scripts/add_temporal.py` (re-run it after any `build_maps.py`
rebuild, which otherwise drops the temporal block from the manifest).

## Publish updates

```bash
git add -A && git commit -m "Update atlas" && git push   # Pages redeploys in ~1 min
```

## Data sources

- Building footprints: **Google Open Buildings** (v3). Borders: ADM0 GeoJSON.
- Training labels: DHS household wealth (IWI), 12 African surveys 2021–2024.
- Part of the PhD project *"Poverty in Space"*. Contact: **y.wang390@lse.ac.uk**.
