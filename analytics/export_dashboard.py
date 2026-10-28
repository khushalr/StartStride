"""Export SQLite analytics tables to CSV for Power BI or Tableau.
Usage: python analytics/export_dashboard.py --db analytics/commuteiq.sqlite --out outputs/bi
"""
import argparse
import csv
import sqlite3
from pathlib import Path

TABLES = ("feed_run", "validation_result", "recommendation_event")
def export(db_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        for table in TABLES:
            # Fixed allowlist prevents SQL identifier injection.
            cursor = con.execute(f"SELECT * FROM {table}")
            with (out_dir / f"{table}.csv").open("w", newline="", encoding="utf-8") as target:
                writer = csv.writer(target)
                writer.writerow([c[0] for c in cursor.description])
                writer.writerows(cursor)
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("outputs/bi"))
    args = p.parse_args()
    export(args.db, args.out)
