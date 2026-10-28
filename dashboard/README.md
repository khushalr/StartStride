# StopStride — Verified TTC Streetcar Analytics Dashboard

This is a **real historical-data** operations dashboard. The public site does not load synthetic records or hypothetical ETAs.

## Source and coverage

- Original dataset: [City of Toronto TTC Streetcar Delay Data](https://open.toronto.ca/dataset/ttc-streetcar-delay-data/)
- Validated archived copy: [University of Toronto SciNet TTC 2014–2025 CSV archive](https://pages.scinet.utoronto.ca/~afedosee/ttc-streetcar-delay-data-2014-2025.zip)
- Raw 2025 CSV SHA256: `eb73f629ea3bdbca0dbdb17f1215b930dadb9ee78885b6a4c871c9fc3b1d38c3`
- Source date range: Jan 1 to Dec 10, 2025 (not a complete calendar year).
- 10,903 original rows; 10,744 validated 2025 rows; 8,377 recorded with Min Delay > 0.
- City CKAN download produced subway-style columns during the first test. The downloader **refuses** that schema and only falls back to U of T's authenticated streetcar CSV when `--fallback-uoft` is passed.

These are reported incidents; route frequency, daily trip counts and passenger exposure are **not available**. Absolute incident totals must not be called per-trip reliability scores.

## Reproduce

```bash
python -m pip install -r requirements.txt
python src/real_data/download_streetcar.py --out outputs/real/source.csv --fallback-uoft
python analytics/build_real_streetcar.py \
  --csv outputs/real/source.csv \
  --source-meta outputs/real/source.source.json \
  --out dashboard/real_data.json \
  --sqlite-db outputs/real/streetcar.sqlite
python analytics/export_real_tables.py --json dashboard/real_data.json --out dashboard/bi
python -m http.server 8000 --directory dashboard
```

Visit `http://localhost:8000` to view the actual recorded-incident analytics. The site checks that `real_data.json` contains `origin=REAL`, a source URL, and SHA256. If those are missing, it displays an error; **no simulated fallback** is ever loaded.

## Real BI outputs

`dashboard/bi/` contains the five actual TTC aggregate CSV datasets, plus `SOURCE.json`:

- `streetcar_routes.csv`
- `streetcar_monthly.csv`
- `streetcar_hourly.csv`
- `streetcar_route_by_hour.csv`
- `streetcar_weekday.csv`

Import these directly into Tableau or Power BI. For route vs month analysis, a native workbook would need a route-by-month table or aggregate the underlying real SQLite records; do not invent a join between route and month from independent summary tables.

**A native Tableau/Power BI project file has not yet been manually created and verified.** These are professional source datasets and a live-tested web visualization, not proof of desktop Tableau expertise by themselves.

## Safe deployment

`.github/workflows/pages.yml` copies *only* `index.html`, `styles.css`, `real_app.js` and `real_data.json` to GitHub Pages and refuses DEMO metadata. It will run on a push to `main` that changes these files, if GitHub Pages is configured to use GitHub Actions.

The original synthetic test scaffolding elsewhere in the repository is not served to visitors.

## Why no live walk-or-wait feature yet?

Streetcar delay logs are historical. They cannot identify a specific streetcar's next-stop ETA. Real recommendation functionality is contingent on validated real-time matching of the same vehicle at consecutive stops, an accessible walking route and measured arrival prediction errors.

## Licensing

Contains information licensed under the Open Government Licence – Toronto. Independent research project, not endorsed by the TTC.
