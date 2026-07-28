# Poverty in Space — Atlas

A static web atlas of **building-based predictions** of wealth, poverty and inequality at
**~5 km resolution across ~49 countries** (Africa + Bangladesh), from **Google Open Buildings**
footprints alone. Every map shows the country border (ADM0).

Each location is a resolution-7 H3 hexagon (~5 km). Seven building-footprint features per hexagon
(density, built-up fraction, mean & spread of footprint size, small/medium/large size shares) feed
**buildings-only gradient-boosted models** trained on 7,442 DHS survey clusters across 12 African
countries.

## Indicators (7)

| Indicator | Definition | CV score |
|---|---|---|
| Wealth | median IWI (0–100) | R² 0.60 |
| Poverty rate | % households IWI < 35 | R² 0.57 |
| Extreme poverty | % households IWI < 20 | R² 0.29 |
| Inequality (CV) | within-hex CV of IWI | R² 0.42 |
| Gini | within-hex Gini of IWI | R² 0.41 |
| Poverty (prob.) | P(median IWI < 35) | AUC 0.88 |
| High inequality (prob.) | P(CV > 0.40) | AUC 0.76 |

**Coverage toggle:** *Screened* = hexes with ≥10 buildings (the model's training floor, where
footprint-shape features are stable); *All buildings* = every populated hex (noisier). Colours use one
fixed scale per indicator across all countries.

Predictions are model estimates, not official statistics — most reliable in Sub-Saharan Africa; North
Africa and small islands are extrapolations; extreme poverty (a rare tail) is the least accurate.

## Live site

**https://Wang-Yifan-1997.github.io/poverty-in-space-atlas/**

## Repository layout

```
index.html                                  # single-page atlas (no build step)
assets/{style.css, app.js, manifest.js}     # manifest.js = window.ATLAS (generated)
figures/
  full/{screening}/{outcome}/{ISO}.png      # titled + colourbar (lightbox)
  thumb/{screening}/{outcome}/{ISO}.png     # clean thumbnails (grid)
  temporal/{full,thumb}/{screening}/{year}/{outcome}/{ISO}.png  # 2.5D 2016 & 2023 panel
data/countries.json                         # manifest: outcomes, screenings, per-country stats
scripts/build_maps.py                       # regenerates every figure + manifest
```

`{screening}` ∈ `screened`, `all`. `{outcome}` ∈ `wealth`, `poverty_rate`, `extreme_rate`,
`inequality_cv`, `gini`, `poverty_dummy`, `inequality_dummy`. `{ISO}` = ISO 3166-1 alpha-3.

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
`train_all_outcomes.py` (7 models) → `predict_all_outcomes.py` → `build_maps.py`.

## Publish updates

```bash
git add -A && git commit -m "Update atlas" && git push   # Pages redeploys in ~1 min
```

## Data sources

- Building footprints: **Google Open Buildings** (v3). Borders: ADM0 GeoJSON.
- Training labels: DHS household wealth (IWI), 12 African surveys 2021–2024.
- Part of the PhD project *"Poverty in Space"*. Contact: **y.wang390@lse.ac.uk**.
