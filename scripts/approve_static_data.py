"""Validate raw GTFS input and copy approved files for app consumption."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ttc_gtfs_qa.engine import run_validations
from ttc_gtfs_qa.io import REQUIRED_FILES, load_gtfs_data
from ttc_gtfs_qa.reporting import build_metrics_report, build_summary_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Approve static GTFS data for live map backend use.")
    parser.add_argument("--raw-path", type=Path, default=Path("data/gtfs_static"))
    parser.add_argument("--approved-path", type=Path, default=Path("data/approved_static"))
    parser.add_argument("--max-high-failures", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = load_gtfs_data(args.raw_path)
    issues, _ = run_validations(data)

    summary = build_summary_report(issues)
    metrics = build_metrics_report(summary)

    high_failures = int(((summary["severity"] == "High") & (summary["status"] == "Fail")).sum())
    pass_rate = float(metrics.loc[metrics["metric"] == "pass_rate_percent", "value"].iloc[0])

    print(f"Validation pass rate: {pass_rate}%")
    print(f"High severity failures: {high_failures}")

    if high_failures > args.max_high_failures:
        print("❌ Approval blocked: high-severity threshold exceeded.")
        return 1

    args.approved_path.mkdir(parents=True, exist_ok=True)

    for filename in REQUIRED_FILES.values():
        shutil.copy2(args.raw_path / filename, args.approved_path / filename)

    for optional in ["calendar.txt", "calendar_dates.txt", "shapes.txt"]:
        src = args.raw_path / optional
        if src.exists():
            shutil.copy2(src, args.approved_path / optional)

    print(f"✅ Approved GTFS copied to: {args.approved_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
