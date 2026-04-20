from __future__ import annotations

from datetime import datetime, timezone

from google.transit import gtfs_realtime_pb2

from app.models.contracts import AlertRecord, RouteRecord, StopRecord, VehicleRecord
from app.services.static_store import StaticDataStore


def _mode_from_route_type(route_type: str | None) -> str:
    if route_type == "0":
        return "streetcar"
    if route_type == "3":
        return "bus"
    return "other"


def normalize_vehicles(
    vehicle_feed: gtfs_realtime_pb2.FeedMessage,
    trip_feed: gtfs_realtime_pb2.FeedMessage,
    alerts: list[AlertRecord],
    static: StaticDataStore,
) -> list[VehicleRecord]:
    route_map = static.route_map()
    trip_map = static.trip_map()
    stop_map = static.stop_map()

    trip_updates: dict[str, tuple[str | None, int | None]] = {}
    for entity in trip_feed.entity:
        if not entity.HasField("trip_update"):
            continue
        trip_id = entity.trip_update.trip.trip_id
        next_stop_id = None
        delay_seconds = None
        for stu in entity.trip_update.stop_time_update:
            if stu.stop_id:
                next_stop_id = stu.stop_id
                if stu.HasField("arrival") and stu.arrival.HasField("delay"):
                    delay_seconds = int(stu.arrival.delay)
                break
        trip_updates[trip_id] = (next_stop_id, delay_seconds)

    alert_routes: dict[str, list[str]] = {}
    for alert in alerts:
        for rid in alert.route_ids:
            alert_routes.setdefault(rid, []).append(alert.alert_id)

    now = datetime.now(timezone.utc)
    records: list[VehicleRecord] = []

    for entity in vehicle_feed.entity:
        if not entity.HasField("vehicle"):
            continue

        vehicle = entity.vehicle
        if not vehicle.vehicle.id:
            continue

        trip_id = vehicle.trip.trip_id if vehicle.trip.trip_id else None
        route_id = vehicle.trip.route_id if vehicle.trip.route_id else None

        trip_meta = trip_map.get(trip_id or "", {})
        if not route_id:
            route_id = trip_meta.get("route_id") or None

        route_meta = route_map.get(route_id or "", {})
        mode = _mode_from_route_type(route_meta.get("route_type"))
        if mode not in {"bus", "streetcar"}:
            continue

        timestamp = datetime.fromtimestamp(vehicle.timestamp, timezone.utc) if vehicle.timestamp else None
        freshness = int((now - timestamp).total_seconds()) if timestamp else None

        next_stop_id, delay_seconds = trip_updates.get(trip_id or "", (None, None))
        direction = trip_meta.get("direction_id")

        records.append(
            VehicleRecord(
                vehicle_id=vehicle.vehicle.id,
                mode=mode,
                route_id=route_id,
                route_short_name=route_meta.get("route_short_name") or None,
                trip_id=trip_id,
                direction_id=int(direction) if str(direction).isdigit() else None,
                headsign=trip_meta.get("trip_headsign") or None,
                lat=vehicle.position.latitude,
                lon=vehicle.position.longitude,
                bearing=vehicle.position.bearing if vehicle.position.HasField("bearing") else None,
                timestamp=timestamp,
                freshness_seconds=freshness,
                next_stop_id=next_stop_id,
                next_stop_name=stop_map.get(next_stop_id or "") or None,
                delay_seconds=delay_seconds,
                alert_ids=alert_routes.get(route_id or "", []),
            )
        )

    return records


def normalize_alerts(alert_feed: gtfs_realtime_pb2.FeedMessage) -> list[AlertRecord]:
    records: list[AlertRecord] = []
    for entity in alert_feed.entity:
        if not entity.HasField("alert"):
            continue
        informed_routes: list[str] = []
        informed_stops: list[str] = []
        for informed in entity.alert.informed_entity:
            if informed.route_id:
                informed_routes.append(informed.route_id)
            if informed.stop_id:
                informed_stops.append(informed.stop_id)

        header = None
        description = None
        if entity.alert.header_text.translation:
            header = entity.alert.header_text.translation[0].text
        if entity.alert.description_text.translation:
            description = entity.alert.description_text.translation[0].text

        records.append(
            AlertRecord(
                alert_id=entity.id or f"alert-{len(records)+1}",
                header=header,
                description=description,
                route_ids=sorted(set(informed_routes)),
                stop_ids=sorted(set(informed_stops)),
                effect=gtfs_realtime_pb2.Alert.Effect.Name(entity.alert.effect)
                if entity.alert.effect is not None
                else None,
                severity_level=gtfs_realtime_pb2.Alert.SeverityLevel.Name(entity.alert.severity_level)
                if entity.alert.severity_level is not None
                else None,
            )
        )
    return records


def normalize_routes(static: StaticDataStore) -> list[RouteRecord]:
    routes = []
    shape_map = static.shape_lines_by_route()
    for route_id, route in static.route_map().items():
        route_type = route.get("route_type")
        mode = _mode_from_route_type(route_type)
        if mode not in {"bus", "streetcar"}:
            continue
        routes.append(
            RouteRecord(
                route_id=route_id,
                route_short_name=route.get("route_short_name") or None,
                route_long_name=route.get("route_long_name") or None,
                route_type=route_type or None,
                mode=mode,
                shape_points=shape_map.get(route_id, []),
            )
        )
    return routes


def normalize_stops(static: StaticDataStore) -> list[StopRecord]:
    if static.stops.empty:
        return []
    rows = []
    for _, row in static.stops.iterrows():
        try:
            rows.append(
                StopRecord(
                    stop_id=str(row.get("stop_id", "")),
                    stop_name=str(row.get("stop_name", "")) or None,
                    lat=float(row.get("stop_lat")),
                    lon=float(row.get("stop_lon")),
                )
            )
        except (TypeError, ValueError):
            continue
    return rows
