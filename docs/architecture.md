# System Architecture

## Components

1. **Static QA layer (`src/ttc_gtfs_qa`)**
   - Validates raw GTFS static files with deterministic rule checks.
   - Produces reproducible reports for governance and triage.

2. **Approval gate (`scripts/approve_static_data.py`)**
   - Runs validations before app ingestion.
   - Blocks promotion if high-severity failures exceed configured threshold.
   - Copies approved files to `data/approved_static/`.

3. **Realtime backend (`backend/app`)**
   - Loads approved static GTFS into lookup maps.
   - Polls GTFS-RT feeds (vehicle positions, trip updates, alerts).
   - Normalizes and enriches vehicle records with static context.
   - Exposes stable internal API for frontend.

4. **Frontend map (`frontend`)**
   - Polls internal APIs on interval.
   - Renders vehicles, routes, stops, and service alerts.
   - Supports route/mode/direction filtering.

## Failure modes and resilience

- Network failures: retry + timeout handling in feed client.
- Feed parsing failures: logged and surfaced in `/api/health` errors.
- Data source unavailability: mock mode keeps UX and development flow working.
- Static data quality degradation: approval gate fails fast on high-severity issues.

## Subway extension plan

MVP intentionally targets buses/streetcars only.

Subway support should be implemented as an additional realtime adapter behind the same normalized contract, so current frontend/API contracts remain stable.
