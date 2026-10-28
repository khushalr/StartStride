"""End-to-end portfolio checks: demo DB -> SQL -> Tableau/Power BI CSVs."""
import csv
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

def run_script(path, *args):
    return subprocess.run([sys.executable, str(ROOT / path), *map(str, args)],
                          cwd=ROOT, check=True, capture_output=True, text=True)


def test_synthetic_demo_and_dashboard_export(tmp_path):
    db = tmp_path / "demo.sqlite"
    run_script("src/run_analytics_demo.py", "--db", db)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM validation_result").fetchone()[0] == 16
        assert conn.execute("SELECT COUNT(*) FROM validation_result WHERE status='FAIL'").fetchone()[0] == 3
        assert conn.execute("SELECT SUM(affected_records) FROM validation_result").fetchone()[0] == 4
        assert conn.execute("SELECT COUNT(*) FROM recommendation_event").fetchone()[0] == 36
        assert conn.execute("SELECT COUNT(*) FROM recommendation_event WHERE action='WALK'").fetchone()[0] > 0
        assert conn.execute("SELECT COUNT(*) FROM recommendation_event WHERE action='WAIT'").fetchone()[0] > 0
        assert conn.execute("SELECT COUNT(*) FROM recommendation_event WHERE data_origin != 'DEMO'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM recommendation_event WHERE caught_vehicle IS NOT NULL").fetchone()[0] == 0
        # SQL dashboard queries are executable on a reproducible example database.
        sql = (ROOT / "analytics" / "dashboard_queries.sql").read_text()
        queries = [q.strip() for q in sql.split(";") if q.strip()]
        results = [conn.execute(query).fetchall() for query in queries]
        assert len(results) == 3
        assert len(results[0]) == 1
        assert len(results[1]) >= 3
        assert results[2] == []  # No fabricated observed catch success!
    out = tmp_path / "bi"
    run_script("analytics/export_dashboard.py", "--db", db, "--out", out)
    with (out / "recommendation_event.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 36
    assert all(r["data_origin"] == "DEMO" for r in rows)


def test_import_qa_report_and_foreign_keys(tmp_path):
    db = tmp_path / "analytics.sqlite"
    run_script("analytics/load_qa_report.py", "--reports", ROOT / "examples" / "sample_reports",
               "--db", db, "--source", "Unit test fixture", "--run-at", "2026-10-27T00:00:00Z")
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT COUNT(*) FROM feed_run").fetchone()[0] == 1
        assert con.execute("SELECT data_origin FROM feed_run").fetchone()[0] == "DEMO"
        assert con.execute("SELECT COUNT(*) FROM validation_result").fetchone()[0] == 16


def test_export_refuses_missing_database(tmp_path):
    proc = subprocess.run([sys.executable, str(ROOT / "analytics" / "export_dashboard.py"),
                           "--db", str(tmp_path / "missing.sqlite"), "--out", str(tmp_path / "bi")],
                          cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode != 0
    assert not (tmp_path / "missing.sqlite").exists()
