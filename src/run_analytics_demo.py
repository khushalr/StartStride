"""Generate a reproducible, explicitly SYNTHETIC SQLite dataset for BI portfolio demos.

Run from repository root: python src/run_analytics_demo.py
No TTC APIs or network connections are used. Will not overwrite an existing DB.
"""
import argparse
import csv
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from commuteiq.decision import recommend

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "analytics" / "schema.sql"
SAMPLE_SUMMARY = ROOT / "examples" / "sample_reports" / "summary_report.csv"
DEFAULT_DB = ROOT / "outputs" / "demo" / "commuteiq.sqlite"


def build_demo(db: Path) -> tuple[int, int]:
    if db.exists():
        raise FileExistsError(f"Refusing to replace existing database: {db}")
    db.parent.mkdir(parents=True, exist_ok=True)
    # Create in exclusive mode, so racing callers cannot overwrite anything.
    con = sqlite3.connect(f"file:{db.resolve()}?mode=rwc", uri=True)
    try:
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
        with SAMPLE_SUMMARY.open(newline="", encoding="utf-8") as f:
            summary = list(csv.DictReader(f))
        if len(summary) != 16:
            raise ValueError("Expected 16 full QA rule rows in sample summary")
        with con:
            cur = con.execute(
                "INSERT INTO feed_run(run_started_at, source_name, data_origin, records_loaded) VALUES(?,?,?,?)",
                ("2026-10-27T08:00:00Z", "SYNTHETIC GTFS QA FIXTURE - NOT TTC OBSERVATIONS", "DEMO", 0),
            )
            run_id = cur.lastrowid
            for row in summary:
                con.execute(
                    "INSERT INTO validation_result(run_id,rule_id,severity,status,affected_records) VALUES(?,?,?,?,?)",
                    (run_id, row["rule_id"], row["severity"], row["status"].upper(), int(row["affected_records"])),
                )
            scenarios = [
                (7, 11, 4, True, 10, True),
                (3, 5, 4, True, 15, True),
                (8, 12, 5, True, 35, True),
                (9, 13, 5, True, 20, False),
                (10, 12, 3, True, 145, True),
                (9, 12, 3, False, 25, True),
                (6, 6, 5, True, 18, True),
                (8, 10, 3, True, 22, True),
                (4, 8, 3, True, 12, True),
                (5, 6, 4, True, 22, True),
                (11, 14, 6, True, 17, True),
                (2, 4, 4, True, 14, True),
            ]
            anchor = datetime(2026, 10, 27, 8, 0, tzinfo=timezone.utc)
            inserted = 0
            for i in range(3):
                for j, (eta_now, eta_next, walk, wants, feed_age, same_vehicle) in enumerate(scenarios):
                    d = recommend(eta_now, eta_next, walk, wants_steps=wants,
                                  feed_age_seconds=feed_age, same_vehicle=same_vehicle)
                    route_id = ("510", "501", "504")[i]
                    moment = anchor + timedelta(minutes=i * 60 + j * 5)
                    con.execute(
                        """INSERT INTO recommendation_event(
                        observed_at, route_id, current_stop_id, next_stop_id, walking_minutes,
                        current_eta_minutes, next_eta_minutes, feed_age_seconds, action,
                        decision_reason, expected_steps, data_origin, caught_vehicle, arrival_observed)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (moment.isoformat(), route_id, f"DEMO-{route_id}-A", f"DEMO-{route_id}-B",
                         d.walking_minutes, eta_now, eta_next, feed_age, d.action,
                         d.reason, d.expected_steps, "DEMO", None, 0),
                    )
                    inserted += 1
        return len(summary), inserted
    except Exception:
        con.close()
        db.unlink(missing_ok=True)  # delete only the newly created demo file
        raise
    finally:
        con.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = p.parse_args()
    count_rules, count_decisions = build_demo(args.db)
    print(f"SYNTHETIC ONLY: {count_rules} QA rules and {count_decisions} decision examples")
    print(f"SQLite demo DB: {args.db}")


if __name__ == "__main__":
    main()
