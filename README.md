# TTC GTFS QA Validation Pipeline

A production-style **data quality pipeline for GTFS static feeds** built with Python and pandas.

This repository validates core GTFS files (routes, trips, stops, stop_times, and optional calendar/shape files), then produces analyst-friendly CSV reports that show what failed, where it failed, and how severe each issue is.

## What this project does (plain English)

Given a GTFS feed, this project:
1. Loads required GTFS tables from disk.
2. Runs a fixed rule set across keys, required fields, relationships, sequencing, time logic, and domain checks.
3. Outputs three reports you can hand to data, planning, or engineering teams:
   - a rule-by-rule status summary,
   - a defect log with sample record IDs,
   - QA metrics (pass rate, failed rules, affected records).

In short: it turns raw transit schedule data into a repeatable QA process with auditable outputs.

---

## Real-world use case: why this matters

Transit teams often use GTFS as the source for dashboards, service planning analysis, and rider-facing systems. If a feed has key or relationship issues (for example, `stop_times.trip_id` values that do not exist in `trips.txt`), downstream analytics and planning decisions can be misleading.

This pipeline helps teams catch those issues **before** publication or analysis by generating concrete, shareable defect evidence.

---

## Architecture / data flow

```text
GTFS input files (data/gtfs_static/*.txt)
        |
        v
Load + validate (src/ttc_gtfs_qa/io.py)
        |
        v
Rule engine (src/ttc_gtfs_qa/engine.py)
  - 16 validation rules
  - modular validator functions
        |
        v
Reporting layer (src/ttc_gtfs_qa/reporting.py)
        |
        v
CSV outputs (outputs/)
  - summary_report.csv
  - defect_log.csv
  - metrics_report.csv
```

---

## Implemented validation coverage

The current rule set includes **16 checks** across:

1. **Primary keys**
   - Duplicate `routes.route_id`
   - Duplicate `trips.trip_id`
   - Duplicate `stops.stop_id`
   - Duplicate composite key `stop_times (trip_id, stop_sequence)`

2. **Required fields**
   - Missing required values in `routes`
   - Missing required values in `trips`
   - Missing required values in `stop_times`

3. **Referential integrity**
   - `trips.route_id -> routes.route_id`
   - `stop_times.trip_id -> trips.trip_id`
   - `stop_times.stop_id -> stops.stop_id`

4. **Sequence and time logic**
   - `stop_sequence` strictly increases within each `trip_id`
   - `departure_time >= arrival_time`

5. **Domain/range and consistency checks**
   - Valid `stop_lat` / `stop_lon` ranges
   - Route-trip consistency
   - `service_id` relationship checks using `calendar.txt` / `calendar_dates.txt` (if present)
   - `shape_id` consistency with `shapes.txt` (if present)

> Note: this is deterministic rule-based QA, not statistical anomaly detection.

---

## Example findings (from included sample reports)

The sample reports in `examples/sample_reports/` show realistic defects such as:
- duplicate stop-time composite keys,
- trips referencing non-existent routes,
- non-increasing stop sequences.

From the included sample metrics:
- total rules: **16**
- failed rules: **3**
- pass rate: **81.25%**
- affected records: **4**

These examples are based on the repository’s bundled sample CSV outputs.

---

## Quick start

### 1) Set up environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Add GTFS files

Place required files in `data/gtfs_static/`:
- `routes.txt`
- `trips.txt`
- `stops.txt`
- `stop_times.txt`

Optional files:
- `calendar.txt`
- `calendar_dates.txt`
- `shapes.txt`

### 3) Run the pipeline

```bash
python src/run_pipeline.py
```

Optional custom paths:

```bash
python src/run_pipeline.py --data-path data/gtfs_static --output-path outputs
```

### 4) Run tests (separate from pipeline execution)

```bash
pytest -q
```

---

## Outputs and how to use them

Running the pipeline writes:

- `outputs/summary_report.csv`  
  Rule-level QA status for tracking trends over time.

- `outputs/defect_log.csv`  
  Failed checks only, with severity and sample IDs for triage.

- `outputs/metrics_report.csv`  
  High-level KPIs for QA reporting (pass rate, failed rules, affected rows).

A practical workflow is:
1. Scan `metrics_report.csv` for overall health,
2. review failed rules in `summary_report.csv`,
3. assign fixes using `defect_log.csv` sample IDs.

---

## Project structure

```text
ttc-gtfs-qa-validation/
├── examples/
│   └── sample_reports/              # reference output CSVs for portfolio/demo use
├── src/
│   ├── run_pipeline.py              # local runner for the QA pipeline
│   └── ttc_gtfs_qa/
│       ├── cli.py                   # CLI argument handling + pipeline orchestration
│       ├── engine.py                # rule definitions and validation execution engine
│       ├── io.py                    # GTFS file loading and output path handling
│       ├── reporting.py             # summary/defect/metrics report builders
│       └── validators/              # modular validation functions
├── tests/
│   ├── test_engine_reporting.py
│   └── test_validators.py
├── requirements.txt
└── README.md
```

---

## Extending the rule set

To add a new validation:
1. Implement a validator in `src/ttc_gtfs_qa/validators/`.
2. Register the rule in `build_rules()` (`src/ttc_gtfs_qa/engine.py`).
3. Add or update tests in `tests/`.

This keeps the codebase lightweight while demonstrating a maintainable QA architecture.
