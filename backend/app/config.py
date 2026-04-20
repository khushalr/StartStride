from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for realtime ingestion and API behavior."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="TTC_", extra="ignore")

    app_name: str = "TTC Live Transit Map API"
    app_env: str = "dev"
    use_mock_data: bool = Field(default=True, description="Use local mock JSON instead of live GTFS-RT feeds")

    static_data_path: str = "data/approved_static"
    mock_payload_path: str = "data/mock/realtime_snapshot.json"

    vehicle_positions_url: str = "https://bustime.ttc.ca/gtfsrt/vehicles"
    trip_updates_url: str = "https://bustime.ttc.ca/gtfsrt/trips"
    alerts_url: str = "https://bustime.ttc.ca/gtfsrt/alerts"

    poll_interval_seconds: int = 20
    request_timeout_seconds: float = 8.0
    request_max_retries: int = 2


settings = Settings()
