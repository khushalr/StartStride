# CommuteIQ: GTFS QA → rider recommendations → operational analytics

## What is built on this branch
- A pure Python decision engine in `src/commuteiq/decision.py`, with unit tests.
- SQLite schema for QA results and recommendation events.
- SQL dashboard queries covering feed quality, recommendation counts and **observed** outcomes.
- SQLite-to-CSV exporter for Tableau or Power BI.
- Importable VBA module that refreshes an Excel workbook and exports its Dashboard sheet as PDF.

**Not yet built:** a live TTC data collector, pedestrian routing, a deployed app, an actual BI workbook, a ready-made Excel workbook, model calibration, or validated real-world outcomes.

## Design principles
1. Preserve existing static GTFS QA as a separate ingestion gate.
2. Source arrival predictions from live GTFS-RT trip updates and identify the SAME trip/vehicle at consecutive stops.
3. Use routable pedestrian distance/time, not straight-line distance; check accessibility and crossings.
4. Show estimated steps only, not medically precise measurements.
5. If predictions are missing, stale, inconsistent, or uncertain, suggest WAIT or show insufficient data.
6. Never use expected steps or a walk recommendation as evidence of an actual completed walk.
7. Collect privacy-minimized aggregate outcomes only with an explicit method for observation; distinguish inferred from verified arrivals.

## Candidate MVP flow
Static GTFS load → QA pipeline → validated stop sequencing → live trip updates (future) →
walking route (future) → decision engine → event database → dashboard exports.

## Build the dashboards
In Tableau Public or Power BI Desktop, import CSVs exported from `analytics/export_dashboard.py`.
Page 1: Feed QA: rules checked, failures, issue trends by run.
Page 2: Recommendation operations: route, hour, WAIT/WALK mix, mean walking time and *potential* steps.
Page 3: Evaluation: verified observation counts, verified catch rates, stale-feed rejection rate (add rejection-reason breakdown).

Never describe a recommendation as a journey or a caught streetcar unless independently observed.

## Workbook + VBA
In Excel, create a workbook with sheets `Dashboard`, `validation_result`, `recommendation_event`, import the CSV data, build pivot tables/charts, and save as .xlsm. Import `excel/CommuteIQReport.bas` through Visual Basic Editor. Run `RefreshAndExportDashboard` to refresh connections and export a PDF.
VBA is desktop Excel-specific and does not execute inside Tableau or on a hosted website.

## Immediate next engineering tasks
- Ingest TTC static GTFS into a relational schema and populate feed_run/validation_result from current report outputs.
- Confirm availability and licensing of real-time streetcar trip updates for consecutive stops.
- Add a pedestrian route service and accessible-path filtering.
- Compare a conservative baseline with real prediction error before recommending walks.
- Add a PWA user interface and logging/monitoring with explicit privacy controls.
