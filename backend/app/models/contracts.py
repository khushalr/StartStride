from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VehicleRecord(BaseModel):
    vehicle_id: str
    mode: str
    route_id: str | None = None
    route_short_name: str | None = None
    trip_id: str | None = None
    direction_id: int | None = None
    headsign: str | None = None
    lat: float
    lon: float
    bearing: float | None = None
    timestamp: datetime | None = None
    freshness_seconds: int | None = None
    next_stop_id: str | None = None
    next_stop_name: str | None = None
    delay_seconds: int | None = None
    alert_ids: list[str] = Field(default_factory=list)


class RouteRecord(BaseModel):
    route_id: str
    route_short_name: str | None = None
    route_long_name: str | None = None
    route_type: str | None = None
    mode: str = "other"
    shape_points: list[list[float]] = Field(default_factory=list)


class StopRecord(BaseModel):
    stop_id: str
    stop_name: str | None = None
    lat: float
    lon: float


class AlertRecord(BaseModel):
    alert_id: str
    header: str | None = None
    description: str | None = None
    route_ids: list[str] = Field(default_factory=list)
    stop_ids: list[str] = Field(default_factory=list)
    effect: str | None = None
    severity_level: str | None = None


class ApiHealth(BaseModel):
    status: str
    mode: str
    last_successful_refresh_utc: datetime | None = None
    age_seconds: int | None = None
    poll_interval_seconds: int
    static_data_loaded: bool
    errors: list[str] = Field(default_factory=list)


class VehiclesResponse(BaseModel):
    updated_at_utc: datetime | None = None
    vehicles: list[VehicleRecord]


class RoutesResponse(BaseModel):
    routes: list[RouteRecord]


class StopsResponse(BaseModel):
    stops: list[StopRecord]


class AlertsResponse(BaseModel):
    alerts: list[AlertRecord]
