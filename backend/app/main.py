from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query

from app.config import settings
from app.models.contracts import AlertsResponse, ApiHealth, RoutesResponse, StopsResponse, VehiclesResponse
from app.services.realtime_state import RealtimeState

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

state = RealtimeState(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    state.load_static()
    await state.refresh_once()
    await state.start()
    logger.info("Realtime polling started")
    yield
    await state.stop()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


@app.get("/api/health", response_model=ApiHealth)
def get_health() -> ApiHealth:
    return state.health()


@app.get("/api/routes", response_model=RoutesResponse)
def get_routes(active_only: bool = Query(default=False)) -> RoutesResponse:
    routes = state.routes
    if active_only:
        active_route_ids = {v.route_id for v in state.vehicles if v.route_id}
        routes = [r for r in routes if r.route_id in active_route_ids]
    return RoutesResponse(routes=routes)


@app.get("/api/stops", response_model=StopsResponse)
def get_stops(min_lat: float | None = None, max_lat: float | None = None) -> StopsResponse:
    stops = state.stops
    if min_lat is not None:
        stops = [s for s in stops if s.lat >= min_lat]
    if max_lat is not None:
        stops = [s for s in stops if s.lat <= max_lat]
    return StopsResponse(stops=stops)


@app.get("/api/alerts", response_model=AlertsResponse)
def get_alerts(route_id: str | None = None) -> AlertsResponse:
    alerts = state.alerts
    if route_id:
        alerts = [a for a in alerts if route_id in a.route_ids]
    return AlertsResponse(alerts=alerts)


@app.get("/api/vehicles", response_model=VehiclesResponse)
def get_vehicles(
    route_id: str | None = None,
    mode: str | None = Query(default=None, pattern="^(bus|streetcar)$"),
    direction_id: int | None = Query(default=None, ge=0, le=1),
) -> VehiclesResponse:
    vehicles = state.vehicles
    if route_id:
        vehicles = [v for v in vehicles if v.route_id == route_id]
    if mode:
        vehicles = [v for v in vehicles if v.mode == mode]
    if direction_id is not None:
        vehicles = [v for v in vehicles if v.direction_id == direction_id]

    return VehiclesResponse(updated_at_utc=state.last_successful_refresh_utc, vehicles=vehicles)
