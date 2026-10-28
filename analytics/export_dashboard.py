"""Export SQLite analytics tables for Power BI and Tableau.

Usage: python analytics/export_dashboard.py --db outputs/demo/commuteiq.sqlite --out outputs/bi
"""
import argparse
import csv
import sqlite3
from pathlib import Path

TABLES = ("feed_run", "validation_result", "recommendation_event")


def export(db_path: Path, out_dir: Path) -> list[Path]:
    if not db_path.is_file():
        raise FileNotFoundError(f"Database does not exist: {db_path}")
    with sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True) as con:
        present = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing = set(TABLES) - present
        if missing:
            raise ValueError(f"Missing analytics tables: {', '.join(sorted(missing))}")
        out_dir.mkdir(parents=True, exist_ok=True)
        files = []
        for table in TABLES:
            cursor = con.execute(f"SELECT * FROM {table} ORDER BY 1")  # fixed table allowlist
            output = out_dir / f"{table}.csv"
            with output.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([c[0] for c in cursor.description])
                writer.writerows(cursor)
            files.append(output)
        return files


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("outputs/bi"))
    args = p.parse_args()
    for filename in export(args.db, args.out):
        print(filename)
