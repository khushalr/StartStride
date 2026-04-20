# Data sources

## Static GTFS

- TTC GTFS schedule feed published via City of Toronto Open Data resources.
- Use this as raw input to the QA validation + approval gate before backend consumption.

## GTFS-Realtime feeds (surface network)

Configured defaults:

- Vehicle positions: `https://bustime.ttc.ca/gtfsrt/vehicles`
- Trip updates: `https://bustime.ttc.ca/gtfsrt/trips`
- Alerts: `https://bustime.ttc.ca/gtfsrt/alerts`

These URLs are environment-configurable in backend settings.

## Source governance

- Keep endpoint URLs in configuration, not hardcoded in frontend.
- Route all realtime access through backend adapters.
- Maintain mock payload compatibility for offline/local development and CI-friendly tests.
