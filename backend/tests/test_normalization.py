from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

pytest.importorskip("google.transit.gtfs_realtime_pb2")

from google.transit import gtfs_realtime_pb2

from app.services.normalization import normalize_alerts, normalize_vehicles
from app.services.static_store import StaticDataStore


def _static_store() -> StaticDataStore:
    store = StaticDataStore(".")
    store.loaded = True
    store.routes = pd.DataFrame(
        [
            {"route_id": "504", "route_short_name": "504", "route_long_name": "King", "route_type": "0"},
            {"route_id": "29", "route_short_name": "29", "route_long_name": "Dufferin", "route_type": "3"},
        ]
    )
    store.trips = pd.DataFrame(
        [
            {"trip_id": "T1", "route_id": "504", "trip_headsign": "To Distillery", "direction_id": "0"},
        ]
    )
    store.stops = pd.DataFrame(
        [
            {"stop_id": "S1", "stop_name": "King St West", "stop_lat": "43.64", "stop_lon": "-79.39"},
        ]
    )
    return store


def test_normalize_vehicles_enriches_with_static_context() -> None:
    vehicles = gtfs_realtime_pb2.FeedMessage()
    entity = vehicles.entity.add()
    entity.id = "veh-1"
    entity.vehicle.vehicle.id = "4401"
    entity.vehicle.trip.trip_id = "T1"
    entity.vehicle.position.latitude = 43.64
    entity.vehicle.position.longitude = -79.39
    entity.vehicle.timestamp = int(datetime.now(timezone.utc).timestamp())

    trips = gtfs_realtime_pb2.FeedMessage()
    t = trips.entity.add()
    t.trip_update.trip.trip_id = "T1"
    stu = t.trip_update.stop_time_update.add()
    stu.stop_id = "S1"
    stu.arrival.delay = 120

    alerts_feed = gtfs_realtime_pb2.FeedMessage()
    a = alerts_feed.entity.add()
    a.id = "alert-1"
    informed = a.alert.informed_entity.add()
    informed.route_id = "504"

    alerts = normalize_alerts(alerts_feed)
    rows = normalize_vehicles(vehicles, trips, alerts, _static_store())

    assert len(rows) == 1
    row = rows[0]
    assert row.mode == "streetcar"
    assert row.route_short_name == "504"
    assert row.next_stop_name == "King St West"
    assert row.delay_seconds == 120
    assert row.alert_ids == ["alert-1"]
