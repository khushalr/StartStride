"""Build a privacy-minimized, static BI dashboard dataset from CommuteIQ SQLite.

Only aggregate counts are exported; no per-rider events or precise stop IDs.
The demo DB is synthetic. Publishing the output to GitHub Pages means it is public.
Usage:
    python dashboard/build_data.py --db outputs/demo/commuteiq.sqlite --out dashboard/data.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _query(con: sqlite3.Connection, sql: str) -> list[dict]:
    cursor = con.execute(sql)
    columns = [c[0] for c in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def build(db: Path, out: Path) -> dict:
    if not db.is_file():
        raise FileNotFoundError(f"SQLite database does not exist: {db}")
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as con:
        required = {"feed_run", "validation_result", "recommendation_event"}
        tables = {row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if not required.issubset(tables):
            raise ValueError(f"Missing tables: {sorted(required - tables)}")

        origins = {row[0] for row in con.execute(
            "SELECT DISTINCT data_origin FROM feed_run UNION "
            "SELECT DISTINCT data_origin FROM recommendation_event")}
        if not origins:
            raise ValueError("Cannot build dashboard without provenance")
        if len(origins) != 1 or next(iter(origins)) not in {"DEMO", "LIVE"}:
            raise ValueError("Refusing to mix synthetic and live records in one public dashboard")
        origin = next(iter(origins))

        qa = _query(con, """
            SELECT f.run_id, f.run_started_at, f.source_name,
                   v.rule_id, v.severity, v.status, v.affected_records
            FROM validation_result v JOIN feed_run f ON f.run_id = v.run_id
            ORDER BY f.run_id, v.rule_id
        """)
        route_actions = _query(con, """
            SELECT route_id, action, COUNT(*) AS events,
                   SUM(CASE WHEN action='WALK' THEN expected_steps ELSE 0 END)
                     AS potential_steps,
                   ROUND(AVG(walking_minutes), 2) AS avg_walking_minutes
            FROM recommendation_event
            GROUP BY route_id, action ORDER BY route_id, action
        """)
        hourly = _query(con, """
            SELECT route_id, substr(observed_at, 12, 2) AS hour_utc, action,
                   COUNT(*) AS events
            FROM recommendation_event
            GROUP BY route_id, substr(observed_at, 12, 2), action
            ORDER BY route_id, hour_utc, action
        """)
        reasons = _query(con, """
            SELECT route_id, action, decision_reason, COUNT(*) AS events
            FROM recommendation_event
            GROUP BY route_id, action, decision_reason
            ORDER BY route_id, events DESC
        """)
        outcomes = _query(con, """
            SELECT route_id,
                   COUNT(*) AS total_events,
                   SUM(CASE WHEN arrival_observed=1 AND caught_vehicle IS NOT NULL
                            THEN 1 ELSE 0 END) AS verified_outcomes,
                   SUM(CASE WHEN arrival_observed=1 AND caught_vehicle=1
                            THEN 1 ELSE 0 END) AS verified_catches
            FROM recommendation_event
            GROUP BY route_id ORDER BY route_id
        """)

    payload = {
        "meta": {
            "product": "CommuteIQ",
            "origin": origin,
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "note": ("Synthetic scenario demonstration; no real riders, actual walks, "
                     "or observed streetcar catches." if origin == "DEMO" else
                     "Locally supplied analytical data; outcome coverage varies."),
            "time_axis": "UTC (event timestamps, not local commute hours)",
        },
        "quality_rules": qa,
        "route_actions": route_actions,
        "hourly": hourly,
        "decision_reasons": reasons,
        "outcomes": outcomes,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("dashboard/data.json"))
    args = p.parse_args()
    data = build(args.db, args.out)
    print(f"Created {args.out} ({data['meta']['origin']} aggregated data)")
