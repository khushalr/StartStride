# Tableau native workbook — StopStride (real TTC 2025 streetcar incidents)

This directory contains a **reproducible Tableau packaged-workbook generator**. It builds a native Tableau `.twbx` containing a `.twb` XML workbook, a CSV of validated **actual TTC incident records**, and original-source attribution. It does **not** generate demo or synthetic observations.

## What is inside

Four Tableau worksheets and a 2×2 dashboard:

| View | Dimensions | Measure | Interpretation |
|---|---|---|---|
| Recorded incidents by route | TTC logged route label | Count of source incident records | Raw volume, not rate of late streetcars |
| Monthly incident trend | Calendar month | Count of source incidents | Archive ends December 10, 2025; last month incomplete |
| Service-delay minutes by route | TTC route label | Sum of logged `Min Delay` | Not rider-minutes or trip delay per passenger |
| Incident counts by hour | Logged time of day | Count of source incidents | Actual log hour, not predicted arrival |

The dataset includes **10,744 validated TTC incident records from Jan 1 – Dec 10, 2025** in the archived original TTC CSV. All rows are reconciled against the independent `dashboard/real_data.json` snapshot. Dates, routes, durations, and hours come from actual log entries.

**Data source:** [TTC Streetcar Delay Data, City of Toronto](https://open.toronto.ca/dataset/ttc-streetcar-delay-data/), retrieved from the [University of Toronto SciNet archive](https://pages.scinet.utoronto.ca/~afedosee/ttc-streetcar-delay-data-2014-2025.zip) when City CKAN supplies mismatched data.

## Build locally

From repository root:

```bash
python -m pip install -r requirements.txt

python src/real_data/download_streetcar.py \
  --out outputs/real/source.csv --fallback-uoft

python analytics/build_real_streetcar.py \
  --csv outputs/real/source.csv \
  --source-meta outputs/real/source.source.json \
  --out outputs/real/report.json

python tableau/build_native.py \
  --source outputs/real/source.csv \
  --source-meta outputs/real/source.source.json \
  --report outputs/real/report.json \
  --out outputs/tableau/StopStride_TTC_2025.twbx
```

The generator verifies the original file's SHA256, source provenance, and the incident count / recorded-delay totals against the real analytics report before packaging anything. A missing file, bad checksum, or mismatched schema is an error.

## Download a prebuilt package

Go to [GitHub Actions](https://github.com/khushalr/StopStride/actions/workflows/tableau.yml), select the latest successful **Build native Tableau workbook from real TTC source** run, and download the `StopStride_TTC_2025_Tableau_REAL` artifact. Unzip the GitHub Actions artifact to obtain the `.twbx`.

## Required manual verification in Tableau Public/Desktop

The GitHub workflow checks XML well-formedness, packaged CSV integrity, and source totals. These checks **do not prove Tableau can successfully open or render** every sheet; Tableau workbook semantics require an actual Tableau application.

1. Open `StopStride_TTC_2025.twbx` in **Tableau Public Desktop** or Tableau Desktop.
2. Check the four worksheets render (not blank or disconnected) and the dashboard opens with all four zones.
3. Verify aggregate counts of **10,744 incident records**, **8,377 positive-delay records**, and **203,665 recorded delay minutes** against `dashboard/real_data.json`. The source has **86 distinct raw route labels**, some of which may reflect labels rather than distinct scheduled routes.
4. If Tableau requests a file location, reconnect the `streetcar_events_2025.csv` source included inside the TWBX; the archive can be opened as a ZIP to extract the file.
5. Inspect the dashboard design and set route/month filters in Tableau as desired. Save the verified workbook via **File → Save As → Tableau Packaged Workbook (.twbx)**, or publish to Tableau Public.
6. Commit/publish that Tableau-verified version and a screenshot. Only then describe it on a resume as a **completed Tableau dashboard**.

**Status: generated package, structurally tested, not yet manually opened in Tableau.** Do not claim a published Tableau Public dashboard until the publish succeeds.

## Relationship to the product

This is **historical transit-operations analytics**, not the live wait-or-walk commuter recommender. The actual consumer feature requires matched GTFS-RT arrival predictions and real pedestrian routing. Neither can be inferred from the historical delay logs.

**Attribution:** Contains information licensed under the Open Government Licence – Toronto. This is an independent research project, not affiliated with or endorsed by the TTC.
