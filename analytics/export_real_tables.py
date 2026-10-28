"""Export only verified real TTC summary tables as Tableau/Power BI-ready CSVs.

python analytics/export_real_tables.py --json dashboard/real_data.json --out dashboard/bi
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

TABLES = {
    "streetcar_routes": ("routes", ["route", "recorded_incidents", "positive_delay_incidents",
                                     "total_recorded_delay_minutes", "avg_recorded_delay_minutes"]),
    "streetcar_monthly": ("monthly", ["month", "recorded_incidents",
                                     "positive_delay_incidents", "recorded_delay_minutes"]),
    "streetcar_hourly": ("hourly", ["hour", "recorded_incidents",
                                   "positive_delay_incidents", "recorded_delay_minutes"]),
    "streetcar_route_by_hour": ("route_by_hour", ["route", "hour", "recorded_incidents",
                                                 "positive_delay_incidents", "recorded_delay_minutes"]),
    "streetcar_weekday": ("weekday", ["day_of_week", "recorded_incidents",
                                     "positive_delay_incidents", "recorded_delay_minutes"]),
}


def export(source: Path, output: Path) -> list[str]:
    obj = json.loads(source.read_text(encoding="utf-8"))
    meta = obj.get("meta", {})
    if meta.get("origin") != "REAL" or not meta.get("source_sha256"):
        raise ValueError("Only source-verified REAL data may be exported")
    output.mkdir(parents=True, exist_ok=True)
    result = []
    for filename, (name, fields) in TABLES.items():
        rows = obj[name]
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"Missing real dataset table: {name}")
        path = output / f"{filename}.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        result.append(str(path))
    (output / "SOURCE.json").write_text(json.dumps(meta, indent=2)+"\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    print("\n".join(export(args.json, args.out)))
