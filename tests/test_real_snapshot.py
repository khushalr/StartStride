"""Contract tests for the published REAL TTC historical analytics snapshot.

These tests use the data actually computed from the original TTC source CSV in
GitHub Actions. No fake incident records are published or loaded by the site.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "dashboard" / "real_data.json"
BI = ROOT / "dashboard" / "bi"


def test_real_ttc_source_provenance_and_accounting():
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    meta, summary = data["meta"], data["summary"]
    assert meta["origin"] == "REAL"
    assert meta["data_kind"].startswith("Historical")
    assert meta["source_page"] == "https://open.toronto.ca/dataset/ttc-streetcar-delay-data/"
    assert meta["source"].startswith("https://")
    assert len(meta["source_sha256"]) == 64
    assert meta["rows_in_source"] >= meta["rows_valid_2025_onward"]
    assert meta["rows_valid_2025_onward"] == summary["recorded_incidents"]
    assert meta["rows_in_source"] - meta["rows_valid_2025_onward"] == meta["rows_dropped_invalid_or_before_2025"]
    assert meta["first_record"] >= "2025-01-01"
    assert meta["last_record"] >= meta["first_record"]
    assert summary["recorded_incidents"] == summary["positive_delay_incidents"] + summary["zero_delay_incidents"]
    assert summary["route_count"] == len(data["routes"])


def test_all_historical_aggregations_balance():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    summary = report["summary"]
    for key in ("routes", "monthly", "hourly", "weekday"):
        rows = report[key]
        assert rows
        assert sum(int(r["recorded_incidents"]) for r in rows) == summary["recorded_incidents"]
        assert sum(int(r["positive_delay_incidents"]) for r in rows) == summary["positive_delay_incidents"]
        duration_name = "total_recorded_delay_minutes" if key == "routes" else "recorded_delay_minutes"
        assert round(sum(float(r[duration_name]) for r in rows), 1) == summary["sum_recorded_delay_minutes"]
    assert sum(r["recorded_incidents"] for r in report["route_by_hour"]) == summary["recorded_incidents"]


def test_tableau_csvs_reconcile_to_actual_ttc_snapshot():
    obj = json.loads(REPORT.read_text(encoding="utf-8"))
    manifest = json.loads((BI / "SOURCE.json").read_text(encoding="utf-8"))
    assert manifest["source_sha256"] == obj["meta"]["source_sha256"]
    for name, json_key in [
        ("streetcar_routes.csv", "routes"),
        ("streetcar_monthly.csv", "monthly"),
        ("streetcar_hourly.csv", "hourly"),
        ("streetcar_route_by_hour.csv", "route_by_hour"),
        ("streetcar_weekday.csv", "weekday"),
    ]:
        with (BI / name).open(encoding="utf-8", newline="") as f:
            data = list(csv.DictReader(f))
        assert len(data) == len(obj[json_key])
        assert sum(int(r["recorded_incidents"]) for r in data) == sum(
            int(r["recorded_incidents"]) for r in obj[json_key]
        )
