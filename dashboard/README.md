# CommuteIQ interactive analytics dashboard

A responsive, no-framework web dashboard that reads **aggregated** SQL outputs. It is a portfolio-grade product prototype and a reference design for a future native Tableau / Power BI report. It is **not** a Tableau workbook.

## View the existing synthetic example

From the repository root:

```bash
python3 -m http.server 8000 --directory dashboard
```

Open [http://localhost:8000](http://localhost:8000).

The checked-in `data.json` contains **synthetic** aggregate data: 36 hypothetical streetcar recommendation events across routes 501, 504, and 510, plus 16 fabricated GTFS QA rule outcomes. It is **not** real TTC performance.

## Regenerate from the actual SQLite analytics layer

```bash
pip install -r requirements.txt
pytest -q
python src/run_analytics_demo.py --db outputs/demo/commuteiq.sqlite
python dashboard/build_data.py --db outputs/demo/commuteiq.sqlite --out dashboard/data.json
python3 -m http.server 8000 --directory dashboard
```

The SQL-backed generator **refuses mixed DEMO/LIVE provenance** and publishes aggregates only, not per-rider rows or stop IDs. Delete the local demo DB or choose another `--db` destination before rerunning the example generator; it intentionally does not overwrite data.

## What the dashboard shows

| View | Measures | Interpretation |
|---|---|---|
| Overview | Decision counts, recommended WALK share, potential steps, route mix, UTC activity, QA pass rate | Recommendations only, not actual activity or arrivals |
| Decision intelligence | Adjustable ETAs, walk duration, safety buffer and route verification controls | Hypothetical decision illustration, **not** a real-time TTC prediction |
| Data quality | Latest run's pass/fail rules, severity and rule-level affected rows | Report integrity, not TTC reliability |

Missing or unverified route/trip conditions yield WAIT. A WALK recommendation never guarantees catching a streetcar.

### Technical implementation

```text
GTFS files → Python QA rules → QA CSV → SQL importer ──┐
                                                       ├→ SQLite → dashboard/build_data.py
Simulated scenario events → Python decision engine ────┘                 ↓
                                                            dashboard/data.json (aggregated)
                                                                         ↓
                                                        browser app.js + logic.js + CSS
```

`dashboard/logic.js` has Node.js unit tests, and `dashboard/build_data.py` has Python integration tests. GitHub Actions runs both.

## Publishing as a website

GitHub Pages can serve this directory using the optional manual deployment workflow `.github/workflows/pages.yml`:

1. Merge the dashboard PR to `main`.
2. In the repository, go to **Settings → Pages → Build and deployment**, set **Source: GitHub Actions**.
3. Open **Actions → Publish CommuteIQ Dashboard → Run workflow** on `main`.
4. The deployment URL appears in the workflow output and under the repository's Pages settings.

Do not publish actual per-person or identifying transit observations. The default checked-in `data.json` is synthetic only. The workflow is intentionally manual to prevent accidental disclosure if local output changes.

## Native Tableau / Power BI build

For a **genuine BI skill demonstration**, create and publish a native report separately:

```bash
python analytics/export_dashboard.py --db outputs/demo/commuteiq.sqlite --out outputs/bi
```

In Tableau Public (or Power BI Desktop), import `outputs/bi/feed_run.csv`, `validation_result.csv`, and `recommendation_event.csv`; relate validation results to runs on `run_id` only, and keep recommendation events independent. Replicate the dashboard's KPI cards, route distribution, action analysis, and QA evidence views. Save a packaged Tableau workbook (`.twbx`) or Power BI (`.pbix`) and add it under `dashboard/native/` after opening it successfully in the corresponding desktop application.

**Do not claim Tableau/Power BI dashboard creation on a resume until that native report exists and has been verified.** This repo currently offers SQL-powered exports and a working web analytics preview, not a native BI file.

## Data provenance

- `DEMO` is simulated. `LIVE` is locally supplied analytic data and does not itself establish a live TTC connection.
- QA violations can overlap; summing affected rows counts rule-level violations, not distinct bad records.
- Potential steps are a rough estimate (walking duration × 110) for **recommended** walks, not health-tracker measurements.
- The application does not collect locations, names, devices, or user data.
