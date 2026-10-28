"""Append an existing QA pipeline report to a local SQLite analytics DB.

Usage:
  python analytics/load_qa_report.py --reports outputs --db outputs/commuteiq.sqlite \
      --origin LIVE --source 'Local GTFS run'
Use DEMO origin for fixture/sample reports. Does not access TTC APIs.
"""
import argparse
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")
ALLOWED_ORIGINS = {"DEMO", "LIVE"}
ALLOWED_STATUSES = {"PASS", "FAIL", "SKIP"}


def import_report(db_path: Path, reports_dir: Path, source: str, origin: str, run_at: str) -> int:
    if origin not in ALLOWED_ORIGINS:
        raise ValueError("origin must be DEMO or LIVE")
    if not source.strip():
        raise ValueError("source cannot be empty")
    with (reports_dir / "summary_report.csv").open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"rule_id", "status", "severity", "affected_records"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"summary_report.csv must contain {sorted(required)}")
        rows = list(reader)
    if not rows:
        raise ValueError("summary_report.csv contains no rules")
    ids = [r["rule_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("rule_id must be unique per report")
    results = []
    for r in rows:
        status = r["status"].strip().upper()
        count = int(r["affected_records"])
        if status not in ALLOWED_STATUSES or count < 0:
            raise ValueError(f"Invalid report row: {r}")
        results.append((r["rule_id"], r["severity"], status, count))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
        with con:
            cur = con.execute(
                "INSERT INTO feed_run(run_started_at,source_name,data_origin,records_loaded) VALUES(?,?,?,?)",
                (run_at, source, origin, 0),
            )
            run_id = cur.lastrowid
            con.executemany(
                "INSERT INTO validation_result(run_id,rule_id,severity,status,affected_records) VALUES(?,?,?,?,?)",
                [(run_id, *row) for row in results],
            )
    return run_id


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reports", type=Path, required=True, help="Folder from src/run_pipeline.py")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--origin", choices=["DEMO", "LIVE"], default="DEMO")
    p.add_argument("--source", default="Local GTFS validation")
    p.add_argument("--run-at", default=datetime.now(timezone.utc).isoformat(), help="UTC ISO timestamp")
    args = p.parse_args()
    new_id = import_report(args.db, args.reports, args.source, args.origin, args.run_at)
    print(f"Imported feed_run={new_id}, source={args.source}, data_origin={args.origin}")
