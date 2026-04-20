from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime, timezone

from app.adapters.gtfs_realtime_client import GTFSRealtimeClient, MockRealtimeClient
from app.config import Settings
from app.models.contracts import AlertRecord, ApiHealth, RouteRecord, StopRecord, VehicleRecord
from app.services.normalization import normalize_alerts, normalize_routes, normalize_stops, normalize_vehicles
from app.services.static_store import StaticDataStore

logger = logging.getLogger(__name__)


class RealtimeState:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.static = StaticDataStore(settings.static_data_path)

        self.vehicles: list[VehicleRecord] = []
        self.routes: list[RouteRecord] = []
        self.stops: list[StopRecord] = []
        self.alerts: list[AlertRecord] = []

        self.last_successful_refresh_utc: datetime | None = None
        self.errors: list[str] = []
        self._task: asyncio.Task | None = None

    def load_static(self) -> None:
        self.static.load()
        self.routes = normalize_routes(self.static)
        self.stops = normalize_stops(self.static)
        logger.info("Loaded static GTFS reference data from %s", self.settings.static_data_path)

    def health(self) -> ApiHealth:
        now = datetime.now(timezone.utc)
        age_seconds = (
            int((now - self.last_successful_refresh_utc).total_seconds())
            if self.last_successful_refresh_utc
            else None
        )
        return ApiHealth(
            status="ok" if not self.errors else "degraded",
            mode="mock" if self.settings.use_mock_data else "live",
            last_successful_refresh_utc=self.last_successful_refresh_utc,
            age_seconds=age_seconds,
            poll_interval_seconds=self.settings.poll_interval_seconds,
            static_data_loaded=self.static.loaded,
            errors=self.errors[-5:],
        )

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _poll_loop(self) -> None:
        while True:
            await self.refresh_once()
            await asyncio.sleep(self.settings.poll_interval_seconds)

    async def refresh_once(self) -> None:
        try:
            if self.settings.use_mock_data:
                payload = MockRealtimeClient(self.settings.mock_payload_path).load_snapshot()
                self.vehicles = [VehicleRecord.model_validate(v) for v in payload.get("vehicles", [])]
                self.alerts = [AlertRecord.model_validate(a) for a in payload.get("alerts", [])]
                self.last_successful_refresh_utc = datetime.now(timezone.utc)
                self.errors = []
                return

            client = GTFSRealtimeClient(
                timeout_seconds=self.settings.request_timeout_seconds,
                max_retries=self.settings.request_max_retries,
            )
            vehicle_feed = client.fetch_feed(self.settings.vehicle_positions_url)
            trip_feed = client.fetch_feed(self.settings.trip_updates_url)
            alert_feed = client.fetch_feed(self.settings.alerts_url)

            alerts = normalize_alerts(alert_feed)
            self.vehicles = normalize_vehicles(vehicle_feed, trip_feed, alerts, self.static)
            self.alerts = alerts
            self.last_successful_refresh_utc = datetime.now(timezone.utc)
            self.errors = []

        except Exception as exc:
            logger.exception("Realtime refresh failed")
            self.errors.append(str(exc))

