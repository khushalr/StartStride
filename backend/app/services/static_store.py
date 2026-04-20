from __future__ import annotations

from pathlib import Path

import pandas as pd


class StaticDataStore:
    """Loads validated static GTFS tables and provides lookup helpers."""

    def __init__(self, data_path: str) -> None:
        self.data_path = Path(data_path)
        self.loaded = False
        self.routes = pd.DataFrame()
        self.trips = pd.DataFrame()
        self.stops = pd.DataFrame()
        self.shapes = pd.DataFrame()

    def load(self) -> None:
        required = {
            "routes": "routes.txt",
            "trips": "trips.txt",
            "stops": "stops.txt",
        }
        optional = {"shapes": "shapes.txt"}

        for key, name in required.items():
            path = self.data_path / name
            if not path.exists():
                raise FileNotFoundError(f"Static GTFS file missing: {path}")
            setattr(self, key, pd.read_csv(path, dtype=str))

        for key, name in optional.items():
            path = self.data_path / name
            if path.exists():
                setattr(self, key, pd.read_csv(path, dtype=str))

        self.loaded = True

    def route_map(self) -> dict[str, dict[str, str]]:
        if self.routes.empty:
            return {}
        cols = [c for c in ["route_id", "route_short_name", "route_long_name", "route_type"] if c in self.routes.columns]
        return {row["route_id"]: row for row in self.routes[cols].fillna("").to_dict(orient="records") if row.get("route_id")}

    def trip_map(self) -> dict[str, dict[str, str]]:
        if self.trips.empty:
            return {}
        cols = [c for c in ["trip_id", "route_id", "trip_headsign", "direction_id", "shape_id"] if c in self.trips.columns]
        return {row["trip_id"]: row for row in self.trips[cols].fillna("").to_dict(orient="records") if row.get("trip_id")}

    def stop_map(self) -> dict[str, str]:
        if self.stops.empty or "stop_id" not in self.stops.columns:
            return {}
        stop_name_col = "stop_name" if "stop_name" in self.stops.columns else None
        out: dict[str, str] = {}
        for _, row in self.stops.iterrows():
            stop_id = str(row.get("stop_id", ""))
            if not stop_id:
                continue
            out[stop_id] = str(row.get(stop_name_col, "")) if stop_name_col else ""
        return out

    def shape_lines_by_route(self) -> dict[str, list[list[float]]]:
        if self.shapes.empty or "shape_id" not in self.shapes.columns:
            return {}
        if self.trips.empty:
            return {}

        shape_to_route = (
            self.trips[["shape_id", "route_id"]]
            .dropna(subset=["shape_id", "route_id"])
            .drop_duplicates()
            .set_index("shape_id")["route_id"]
            .to_dict()
        )
        required_cols = {"shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"}
        if not required_cols.issubset(set(self.shapes.columns)):
            return {}

        frame = self.shapes.copy()
        frame = frame.dropna(subset=["shape_pt_lat", "shape_pt_lon"]) 
        frame["shape_pt_sequence"] = pd.to_numeric(frame["shape_pt_sequence"], errors="coerce")
        frame = frame.sort_values(["shape_id", "shape_pt_sequence"])

        out: dict[str, list[list[float]]] = {}
        for shape_id, grp in frame.groupby("shape_id"):
            route_id = shape_to_route.get(shape_id)
            if not route_id:
                continue
            coords = grp[["shape_pt_lat", "shape_pt_lon"]].astype(float).values.tolist()
            if coords:
                out.setdefault(route_id, coords)
        return out
