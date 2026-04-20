"""Command-line entry point for GTFS QA validation."""

from __future__ import annotations

import argparse
from pathlib import Path

from ttc_gtfs_qa.engine import run_validations
from ttc_gtfs_qa.io import DATA_PATH, OUTPUT_PATH, ensure_output_path, load_gtfs_data
from ttc_gtfs_qa.reporting import (
    build_defect_log,
    build_metrics_report,
    build_summary_report,
    save_reports,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line options for pipeline execution."""
    parser = argparse.ArgumentParser(
        prog="ttc-gtfs-qa",
        description="Run GTFS static feed data-quality validations and export CSV reports.",
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DATA_PATH,
        help="Directory containing GTFS input text files (default: data/gtfs_static).",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=OUTPUT_PATH,
        help="Directory where CSV reports will be written (default: outputs).",
    )
    return parser.parse_args()


def main() -> None:
    """Run the GTFS data-quality pipeline and write CSV reports."""
    args = parse_args()
    ensure_output_path(args.output_path)

    print(f"Loading GTFS data from: {args.data_path}")
    data = load_gtfs_data(args.data_path)

    print("Running validation checks...")
    issues, issue_frames = run_validations(data)

    summary_df = build_summary_report(issues)
    defect_df = build_defect_log(issues, issue_frames)
    metrics_df = build_metrics_report(summary_df)

    save_reports(summary_df, defect_df, metrics_df, args.output_path)

    print("Validation complete.")
    print(f"- {args.output_path / 'summary_report.csv'}")
    print(f"- {args.output_path / 'defect_log.csv'}")
    print(f"- {args.output_path / 'metrics_report.csv'}")


if __name__ == "__main__":
    main()
