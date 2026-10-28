"""Regression tests for SQL-to-dashboard analytics and data provenance."""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run_script(path: str, *args):
    return subprocess.run([sys.executable, str(ROOT / path), *map(str, args)],
                          cwd=ROOT, check=True, capture_output=True, text=True)


def test_dashboard_aggregations_and_provenance(tmp_path):
    db = tmp_path / "demo.sqlite"
    out = tmp_path / "data.json"
    run_script("src/run_analytics_demo.py", "--db", db)
    run_script("dashboard/build_data.py", "--db", db, "--out", out)
    payload = json.loads(out.read_text())
    assert payload["meta"]["origin"] == "DEMO"
    assert len(payload["quality_rules"]) == 16
    assert sum(r["status"] == "FAIL" for r in payload["quality_rules"]) == 3
    assert sum(r["affected_records"] for r in payload["quality_rules"]) == 4
    assert sum(r["events"] for r in payload["route_actions"]) == 36
    assert sum(r["events"] for r in payload["route_actions"] if r["action"] == "WALK") == 15
    assert sum(r["potential_steps"] for r in payload["route_actions"]) == 6930
    assert sum(r["verified_outcomes"] for r in payload["outcomes"]) == 0
    assert {r["route_id"] for r in payload["outcomes"]} == {"501", "504", "510"}
    # Safe aggregate output must not reveal exact stop IDs or event rows.
    assert "current_stop_id" not in out.read_text()
    assert "next_stop_id" not in out.read_text()
    assert "observed_at" not in out.read_text()


def test_dashboard_rejects_mixed_origins(tmp_path):
    db = tmp_path / "demo.sqlite"
    out = tmp_path / "data.json"
    run_script("src/run_analytics_demo.py", "--db", db)
    with sqlite3.connect(db) as con:
        con.execute("UPDATE recommendation_event SET data_origin='LIVE' WHERE event_id=1")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "dashboard/build_data.py"), "--db", str(db), "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode != 0
    assert not out.exists()


def test_dashboard_rejects_missing_db(tmp_path):
    out = tmp_path / "data.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "dashboard/build_data.py"),
         "--db", str(tmp_path / "missing.sqlite"), "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode != 0
    assert not out.exists()
