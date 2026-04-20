# TTC GTFS QA + Live Transit Map Platform

A portfolio-ready transit data engineering project that combines:

1. **Static GTFS data quality validation** (existing Python/pandas rule engine), and
2. **A full-stack live transit map MVP** for TTC surface vehicles (bus + streetcar).

The result is a realistic architecture: validated schedule data powers a realtime ingestion backend and a map frontend that shows live vehicles, route context, and service alerts.

---

## Problem this project solves

Transit apps are only as reliable as their data pipeline.

- If static GTFS keys/relationships are broken, realtime joins degrade.
- If realtime ingestion is fragile, map freshness and rider trust drop.

This project demonstrates an end-to-end approach:

**raw GTFS -> QA gate -> approved static GTFS -> realtime ingestion + normalization -> frontend map + APIs**

---

## MVP scope (implemented)

### Surface transit map (bus + streetcar)
- Full-city map view centered on Toronto.
- Live vehicle markers with icon differentiation (bus vs streetcar).
- Route filtering, mode filtering, direction filtering.
- Vehicle popup details:
  - route/branch context,
  - vehicle id,
  - trip id,
  - headsign (if available),
  - feed freshness,
  - next stop + delay (if available).
- Route shapes rendered on map.
- Stop markers shown at higher zoom.
- Alerts panel sourced from backend `/api/alerts`.
- Polling refresh loop for live updates.
- Marker clustering strategy for high marker density.

### Backend + API
- FastAPI backend with polling ingestion loop.
- GTFS-RT parsing for:
  - vehicle positions,
  - trip updates,
  - alerts.
- Normalized server-side vehicle model for frontend consumption.
- Internal API endpoints:
  - `GET /api/vehicles`
  - `GET /api/routes`
  - `GET /api/stops`
  - `GET /api/alerts`
  - `GET /api/health`
- Mock mode for local development when live feed access is unavailable.

### Static data quality gate (reused validator)
- Existing 16-rule GTFS QA engine remains intact.
- Added an approval step script that blocks promotion if high-severity failures exceed threshold.
- Approved static data is copied to `data/approved_static/` for backend use.

---

## Architecture / data flow

```text
Raw GTFS files (data/gtfs_static/*.txt)
          |
          v
QA validation engine (src/ttc_gtfs_qa/*)
  - summary_report.csv
  - defect_log.csv
  - metrics_report.csv
          |
          v
Approval gate (scripts/approve_static_data.py)
  - blocks release on high-severity failures
  - writes approved files to data/approved_static/
          |
          v
FastAPI backend (backend/app)
  - loads approved static GTFS
  - polls GTFS-RT feeds (or mock JSON)
  - normalizes + joins static/realtime context
  - caches latest app-ready state
          |
          v
Frontend map app (frontend/)
  - fetches internal APIs only
  - renders vehicles, shapes, stops, alerts
  - route/mode/direction filtering
```

---

## Repository structure

```text
ttc-gtfs-qa-validation/
├── backend/
│   ├── app/
│   │   ├── adapters/                # GTFS-RT HTTP + mock adapters
│   │   ├── models/                  # API contracts (Pydantic)
│   │   ├── services/                # static store, normalization, realtime state
│   │   ├── config.py
│   │   └── main.py                  # FastAPI app + API routes
│   ├── tests/
│   └── requirements.txt
├── data/
│   ├── approved_static/             # validated static GTFS used by backend
│   └── mock/                        # offline realtime snapshot for local dev
├── docs/
│   ├── architecture.md
│   └── data_sources.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── lib/
│   └── package.json
├── scripts/
│   └── approve_static_data.py       # QA gate -> approved static data
├── src/ttc_gtfs_qa/                 # existing GTFS QA package
└── tests/                           # existing validator tests
```

---

## Quickstart

## 1) Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Validate raw static GTFS + approve for app use

Put raw GTFS schedule files under `data/gtfs_static/` and run:

```bash
PYTHONPATH=src python scripts/approve_static_data.py --raw-path data/gtfs_static --approved-path data/approved_static
```

If high-severity failures exceed threshold, the command exits non-zero and approval is blocked.

## 3) Run backend API

```bash
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
```

Backend default mode is mock for easy local startup (`TTC_USE_MOCK_DATA=true`).

## 4) Run frontend map

```bash
cd frontend
npm install
npm run dev
```

Frontend expects backend at `http://localhost:8000` by default.
Override with `VITE_API_BASE`.

---

## API examples

```bash
curl "http://localhost:8000/api/health"
curl "http://localhost:8000/api/vehicles?mode=streetcar"
curl "http://localhost:8000/api/routes?active_only=true"
```

---

## Environment variables (backend)

All backend variables use `TTC_` prefix:

- `TTC_USE_MOCK_DATA` (`true|false`)
- `TTC_STATIC_DATA_PATH` (default `data/approved_static`)
- `TTC_MOCK_PAYLOAD_PATH` (default `data/mock/realtime_snapshot.json`)
- `TTC_VEHICLE_POSITIONS_URL` (default `https://bustime.ttc.ca/gtfsrt/vehicles`)
- `TTC_TRIP_UPDATES_URL` (default `https://bustime.ttc.ca/gtfsrt/trips`)
- `TTC_ALERTS_URL` (default `https://bustime.ttc.ca/gtfsrt/alerts`)
- `TTC_POLL_INTERVAL_SECONDS` (default `20`)
- `TTC_REQUEST_TIMEOUT_SECONDS` (default `8`)
- `TTC_REQUEST_MAX_RETRIES` (default `2`)

---

## Screenshots

Frontend screenshot placeholder (generate after running locally):

- `docs/assets/live-map-placeholder.png` (not yet committed)

---

## Why this is portfolio-strong

- Demonstrates **data quality engineering + backend systems + frontend mapping** in one cohesive project.
- Uses a realistic transit-domain architecture with clear separation of concerns.
- Handles offline development with mock mode while keeping clean live-feed integration points.
- Keeps scope disciplined: MVP is TTC surface network first; subway expansion is a planned extension.

---

## Future extensions

- Add subway train positions through a separate adapter once an official source is confirmed.
- Persist short rolling vehicle history for movement trails.
- Add route-focused deep links (`/route/:routeId`).
- Add richer alert-to-shape visualization for detours.
