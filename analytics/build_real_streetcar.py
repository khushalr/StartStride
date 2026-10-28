"""Analyze ACTUAL TTC streetcar delay incidents; reject demo provenance.

Output is historical incident analytics, NOT live streetcar arrival predictions,
vehicle frequency, rider-level delay, or a wait-versus-walk recommendation.

python analytics/build_real_streetcar.py --csv outputs/real/source.csv \
    --source-meta outputs/real/source.source.json --out dashboard/real_data.json
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path
import pandas as pd

NEEDED = {"date", "route", "time", "min delay"}


def build(csv_path: Path, source_meta: Path, out: Path, sqlite_path: Path | None = None) -> dict:
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)
    meta = json.loads(source_meta.read_text(encoding="utf-8"))
    if meta.get("origin") != "REAL" or not meta.get("source") or not meta.get("sha256"):
        raise ValueError("Source manifest must prove REAL origin, URL and SHA256")
    import hashlib
    actual_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if actual_sha != meta["sha256"]:
        raise ValueError("Input CSV SHA256 disagrees with provenance manifest")
    try:
        frame = pd.read_csv(csv_path, dtype=str, encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        frame = pd.read_csv(csv_path, dtype=str, encoding="cp1252", low_memory=False)
    frame.columns = [c.strip().lower().replace('report.date','date').replace('min.delay','min delay').replace('min.gap','min gap') for c in frame.columns]
    if not NEEDED.issubset(frame.columns):
        raise ValueError(f"Missing fields: {sorted(NEEDED - set(frame.columns))}")
    rows_read = len(frame)
    if rows_read == 0:
        raise ValueError("Empty source data; nothing to publish")

    # Datetimes in TTC archives vary. Preserve invalid rows in quality accounting.
    dates = pd.to_datetime(frame["date"].str.strip(), dayfirst=True, errors="coerce")
    # Fallback ISO formats if source uses YYYY-MM-DD.
    bad = dates.isna()
    if bad.any():
        dates.loc[bad] = pd.to_datetime(frame.loc[bad, "date"], errors="coerce")
    route = frame["route"].fillna("").astype(str).str.strip()
    hour = pd.to_numeric(frame["time"].fillna("").str.extract(r"^\s*(\d{1,2}):\d{2}")[0],
                         errors="coerce")
    delay_string = frame["min delay"].replace({
        "None": None, "none": None, "": None, "NULL": None, "nan": None})
    delay = pd.to_numeric(delay_string, errors="coerce")
    # Do not mistake missing "None" duration for zero minutes.
    valid = (dates.notna() & route.ne("") &
             hour.between(0, 23, inclusive="both") &
             delay.notna() & delay.ge(0))
    data = pd.DataFrame({
        "date": dates.loc[valid],
        "route": route.loc[valid],
        "hour": hour.loc[valid].astype(int),
        "minutes": delay.loc[valid].astype(float),
    })
    if len(data) < 100:
        raise ValueError("Too few valid real TTC incident rows to publish")
    if (data["date"].dt.year < 2014).any() or (data["date"].dt.year > datetime.now().year).any():
        raise ValueError("Unexpected dates; check source schema or parsing")
    if not data["date"].dt.year.ge(2025).any():
        raise ValueError("Source has no records from 2025 onward")
    # Use current-format records only for comparability. Never mix pre-2025 free-text
    # and post-2025 incident categories and imply like-for-like causes.
    data = data.loc[data["date"].dt.year.ge(2025)]
    if data.empty:
        raise ValueError("No 2025+ incidents present")
    data["month"] = data["date"].dt.strftime("%Y-%m")
    data["day_of_week"] = data["date"].dt.day_name()
    data["positive"] = data["minutes"] > 0
    positive = data.loc[data["positive"]]

    # Materialize the validated ACTUAL TTC incidents in a relational SQLite table.
    # This supports analyst SQL queries, reproducible BI exports and interviews.
    if sqlite_path is not None:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(sqlite_path) as con:
            with con:
                con.execute("DROP TABLE IF EXISTS streetcar_incident")
                con.execute("""CREATE TABLE streetcar_incident (
                    incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_date TEXT NOT NULL,
                    route TEXT NOT NULL,
                    hour INTEGER NOT NULL CHECK(hour BETWEEN 0 AND 23),
                    delay_minutes REAL NOT NULL CHECK(delay_minutes >= 0),
                    source_sha256 TEXT NOT NULL)""")
                con.executemany(
                    """INSERT INTO streetcar_incident(
                        record_date, route, hour, delay_minutes, source_sha256)
                        VALUES (?, ?, ?, ?, ?)""",
                    ((row.date.strftime("%Y-%m-%d"), row.route, int(row.hour),
                      float(row.minutes), meta["sha256"])
                     for row in data.itertuples(index=False))
                )
                con.execute("CREATE INDEX idx_streetcar_route_time ON streetcar_incident(route, record_date, hour)")
                actual = con.execute("SELECT COUNT(*) FROM streetcar_incident").fetchone()[0]
                if actual != len(data):
                    raise ValueError("SQLite row count does not match validated TTC data")

    def groups(cols: list[str]) -> list[dict]:
        result = data.groupby(cols, dropna=False).agg(
            recorded_incidents=("minutes", "size"),
            positive_delay_incidents=("positive", "sum"),
            recorded_delay_minutes=("minutes", "sum")
        ).reset_index().sort_values(cols)
        result["recorded_delay_minutes"] = result["recorded_delay_minutes"].round(1)
        return result.to_dict(orient="records")

    routes = data.groupby("route").agg(
        recorded_incidents=("minutes", "size"),
        positive_delay_incidents=("positive", "sum"),
        total_recorded_delay_minutes=("minutes", "sum"),
        avg_recorded_delay_minutes=("minutes", "mean"),
    ).reset_index()
    routes = routes.sort_values("recorded_incidents", ascending=False)
    routes["total_recorded_delay_minutes"] = routes["total_recorded_delay_minutes"].round(1)
    routes["avg_recorded_delay_minutes"] = routes["avg_recorded_delay_minutes"].round(2)
    output = {
        "meta": {
            "origin": "REAL",
            "mode": "streetcar",
            "data_kind": "Historical TTC logged incidents; NOT real-time arrivals",
            "source": meta["source"],
            "source_page": meta["official_dataset_page"],
            "retrieval": meta["retrieval"],
            "source_sha256": meta["sha256"],
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "first_record": data["date"].min().strftime("%Y-%m-%d"),
            "last_record": data["date"].max().strftime("%Y-%m-%d"),
            "rows_in_source": int(rows_read),
            "rows_valid_2025_onward": int(len(data)),
            "rows_dropped_invalid_or_before_2025": int(rows_read-len(data)),
            "note": "Counts are logged TTC incidents, NOT delays per vehicle, reliability per trip or riders delayed.",
        },
        "summary": {
            "recorded_incidents": int(len(data)),
            "positive_delay_incidents": int(len(positive)),
            "zero_delay_incidents": int((data["minutes"]==0).sum()),
            "sum_recorded_delay_minutes": round(float(data["minutes"].sum()),1),
            "median_positive_delay_minutes": (round(float(positive["minutes"].median()),1)
                                              if len(positive) else None),
            "route_count": int(data["route"].nunique()),
        },
        "routes": routes.to_dict(orient="records"),
        "monthly": groups(["month"]),
        "hourly": groups(["hour"]),
        "route_by_hour": groups(["route", "hour"]),
        "weekday": groups(["day_of_week"]),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--source-meta", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sqlite-db", type=Path, default=None,
                        help="Optional destination for validated real incident-level SQLite table")
    args = parser.parse_args()
    result = build(args.csv, args.source_meta, args.out, args.sqlite_db)
    print(json.dumps({"source": result["meta"]["source"], "last_record": result["meta"]["last_record"],
                      "summary": result["summary"]}, indent=2))
