from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import requests
from google.transit import gtfs_realtime_pb2

logger = logging.getLogger(__name__)


class GTFSRealtimeClient:
    """Fetch GTFS-RT protobuf feeds with basic retry handling."""

    def __init__(self, timeout_seconds: float, max_retries: int) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def fetch_feed(self, url: str) -> gtfs_realtime_pb2.FeedMessage:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                response = requests.get(url, timeout=self.timeout_seconds)
                response.raise_for_status()
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(response.content)
                return feed
            except Exception as exc:  # network and parse errors
                last_error = exc
                logger.warning("Failed fetching GTFS-RT feed %s (attempt %s): %s", url, attempt, exc)
                time.sleep(min(attempt, 3))
        raise RuntimeError(f"Unable to fetch GTFS-RT feed: {url}") from last_error


class MockRealtimeClient:
    """Loads pre-normalized local JSON snapshot for offline development."""

    def __init__(self, payload_path: str) -> None:
        self.payload_path = Path(payload_path)

    def load_snapshot(self) -> dict:
        if not self.payload_path.exists():
            raise FileNotFoundError(f"Mock payload file not found: {self.payload_path}")
        return json.loads(self.payload_path.read_text())
