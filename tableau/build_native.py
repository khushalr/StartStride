"""Build a Tableau .twbx from real TTC 2025 streetcar incident records only.

This creates a native Tableau XML workbook and packages a sanitized incident
CSV in a TWBX ZIP. Tableau rendering still requires verification in the actual
Tableau application. Source data must reconcile with dashboard/real_data.json.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree as E

import pandas as pd

NAME = "StopStride_TTC_2025.twb"
DATA_FILE = "streetcar_events_2025.csv"
FOLDER = "Data/StopStride_TTC_2025"
DS = "federated.stopstride2025"
CONN = "textscan.stopstride2025"
FIELDS = [
    ("record_date", "date", "dimension", "ordinal"),
    ("month", "string", "dimension", "nominal"),
    ("route", "string", "dimension", "nominal"),
    ("hour", "integer", "dimension", "ordinal"),
    ("delay_minutes", "real", "measure", "quantitative"),
    ("incident_count", "integer", "measure", "quantitative"),
    ("positive_delay_flag", "integer", "measure", "quantitative"),
]
VIEWS = [
    ("Route | recorded incidents", "route", "incident_count", "Bar", "#79DDB9"),
    ("Monthly | recorded incidents", "month", "incident_count", "Line", "#79DDB9"),
    ("Route | service-delay minutes", "route", "delay_minutes", "Bar", "#E8B984"),
    ("Hour | recorded incidents", "hour", "incident_count", "Bar", "#77B9D0"),
]


def add(parent, tag, **attributes):
    return E.SubElement(parent, tag, {k.replace("_", "-"): str(v) for k, v in attributes.items()})


def guid(value):
    return "{" + str(uuid.uuid5(uuid.NAMESPACE_DNS, "stopstride:" + value)).upper() + "}"


def validated_records(source: Path, manifest: Path, report: Path) -> tuple[bytes, dict]:
    info = json.loads(manifest.read_text(encoding="utf-8"))
    snapshot = json.loads(report.read_text(encoding="utf-8"))
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if (info.get("origin") != "REAL" or digest != info.get("sha256")
            or digest != snapshot.get("meta", {}).get("source_sha256")
            or snapshot["meta"]["origin"] != "REAL"):
        raise ValueError("Real TTC data provenance and SHA256 verification failed")
    df = pd.read_csv(io.BytesIO(raw), dtype=str, low_memory=False)
    df.columns = [
        c.strip().lower().replace("report.date", "date").replace("min.delay", "min delay")
        for c in df.columns
    ]
    if not {"date", "route", "time", "min delay"}.issubset(df.columns):
        raise ValueError("Unexpected streetcar input schema")
    dates = pd.to_datetime(df["date"].str.strip(), dayfirst=True, errors="coerce")
    if dates.isna().any():
        missing = dates.isna()
        dates.loc[missing] = pd.to_datetime(df.loc[missing, "date"], errors="coerce")
    routes = df["route"].fillna("").str.strip()
    hours = pd.to_numeric(df["time"].fillna("").str.extract(r"^\s*(\d{1,2}):\d{2}")[0], errors="coerce")
    delay = pd.to_numeric(df["min delay"], errors="coerce")
    valid = dates.notna() & routes.ne("") & hours.between(0, 23) & delay.notna() & delay.ge(0)
    rows = pd.DataFrame({
        "record_date": dates.loc[valid], "route": routes.loc[valid],
        "hour": hours.loc[valid].astype(int),
        "delay_minutes": delay.loc[valid].astype(float),
    })
    rows = rows[rows["record_date"].dt.year.ge(2025)].copy()
    rows["month"] = rows["record_date"].dt.strftime("%Y-%m")
    rows["record_date"] = rows["record_date"].dt.strftime("%Y-%m-%d")
    rows["incident_count"] = 1
    rows["positive_delay_flag"] = (rows["delay_minutes"] > 0).astype(int)
    rows = rows[[field[0] for field in FIELDS]]
    expected = snapshot["summary"]
    measured = (
        len(rows),
        int(rows["positive_delay_flag"].sum()),
        round(float(rows["delay_minutes"].sum()), 1),
    )
    declared = (
        expected["recorded_incidents"],
        expected["positive_delay_incidents"],
        expected["sum_recorded_delay_minutes"],
    )
    if measured != declared or len(rows) < 100:
        raise ValueError(f"Real TTC event dataset does not reconcile: {measured} vs {declared}")
    buff = io.StringIO()
    rows.to_csv(buff, index=False, lineterminator="\n")
    return buff.getvalue().encode("utf-8"), snapshot


def native_xml() -> bytes:
    root = E.Element("workbook", {
        "original-version": "18.1", "source-build": "2025.1",
        "source-platform": "win", "version": "18.1",
    })
    sources = add(root, "datasources")
    ds = add(sources, "datasource", name=DS,
             caption="REAL TTC streetcar incidents | 2025", inline="true", version="18.1")
    conn = add(ds, "connection", **{"class": "federated"})
    named = add(conn, "named-connections")
    nc = add(named, "named-connection", caption="TTC recorded streetcar incidents 2025", name=CONN)
    add(nc, "connection", **{
        "class": "textscan", "directory": FOLDER, "filename": DATA_FILE,
        "password": "", "server": ""
    })
    rel = add(conn, "relation", connection=CONN, name=DATA_FILE,
              table="[streetcar_events_2025#csv]", type="table")
    cols = add(rel, "columns", **{
        "character-set": "UTF-8", "header": "yes", "locale": "en_US", "separator": ","
    })
    for index, (field, dtype, _, _) in enumerate(FIELDS):
        add(cols, "column", name=field, datatype=dtype, ordinal=index)
    records = add(conn, "metadata-records")
    for index, (field, dtype, _, _) in enumerate(FIELDS):
        record = add(records, "metadata-record", **{"class": "column"})
        for tag, value in [
            ("remote-name", field), ("remote-type", {
                "string": 129, "date": 133, "integer": 20, "real": 5
            }[dtype]), ("local-name", f"[{field}]"),
            ("parent-name", f"[{DATA_FILE}]"), ("remote-alias", field),
            ("ordinal", index), ("local-type", dtype),
            ("aggregation", "Sum" if dtype in {"real", "integer"} else "Count"),
            ("contains-null", "false"),
        ]:
            add(record, tag).text = str(value)
    add(ds, "aliases", enabled="yes")
    for field, dtype, role, fieldtype in FIELDS:
        add(ds, "column", caption=field.replace("_", " ").title(),
            datatype=dtype, name=f"[{field}]", role=role, type=fieldtype)
    add(ds, "layout", **{
        "dim-ordering": "alphabetic",
        "measure-ordering": "alphabetic", "show-structure": "true"
    })

    sheets = add(root, "worksheets")
    for title, dimension, measure, mark, color in VIEWS:
        sheet = add(sheets, "worksheet", name=title)
        add(add(add(sheet, "layout-options"), "title"), "formatted-text")
        add(sheet.find("./layout-options/title/formatted-text"), "run").text = title
        table = add(sheet, "table")
        view = add(table, "view")
        add(add(view, "datasources"), "datasource",
            name=DS, caption="REAL TTC streetcar incidents | 2025")
        dep = add(view, "datasource-dependencies", datasource=DS)
        for field, derivation in ((dimension, "None"), (measure, "Sum")):
            dtype, role = next((x[1], x[2]) for x in FIELDS if x[0] == field)
            add(dep, "column", datatype=dtype, name=f"[{field}]", role=role,
                type="nominal" if role == "dimension" else "quantitative")
            add(dep, "column-instance", column=f"[{field}]", derivation=derivation,
                name=f"[{'none' if derivation == 'None' else 'sum'}:{field}:{'nk' if derivation == 'None' else 'qk'}]",
                pivot="key", type="nominal" if derivation == "None" else "quantitative")
        add(view, "aggregation", value="true")
        add(table, "style")
        pane = add(add(table, "panes"), "pane", **{
            "selection-relaxation-option": "selection-relaxation-allow"
        })
        add(add(pane, "view"), "breakdown", value="auto")
        add(pane, "mark", **{"class": mark})
        style = add(add(pane, "style"), "style-rule", element="mark")
        add(style, "format", attr="mark-color", value=color)
        add(style, "format", attr="mark-labels-show", value="true")
        dimension_ref = f"[{DS}].[none:{dimension}:nk]"
        measure_ref = f"[{DS}].[sum:{measure}:qk]"
        add(table, "rows").text = dimension_ref if dimension == "route" else measure_ref
        add(table, "cols").text = measure_ref if dimension == "route" else dimension_ref
        add(sheet, "simple-id", uuid=guid(title))

    board_name = "StopStride | 2025 TTC streetcar incident intelligence"
    board = add(add(root, "dashboards"), "dashboard",
                name=board_name, **{"enable-sort-zone-taborder": "true"})
    add(board, "style")
    add(board, "size", maxheight=900, maxwidth=1400, minheight=900, minwidth=1400)
    parent = add(add(board, "zones"), "zone", id=1, x=0, y=0, w=100000, h=100000,
                 **{"type-v2": "layout-basic"})
    for index, (title, *_) in enumerate(VIEWS):
        add(parent, "zone", id=index + 2, name=title,
            x=800 if index % 2 == 0 else 50400,
            y=1000 if index < 2 else 50600, w=48800, h=48400)
    add(board, "simple-id", uuid=guid(board_name))

    windows = add(root, "windows", **{"source-height": "30"})
    for title, *_ in VIEWS:
        window = add(windows, "window", **{"class": "worksheet", "name": title})
        cards = add(window, "cards")
        left = add(cards, "edge", name="left")
        strip = add(left, "strip", size=160)
        for kind in ("pages", "filters", "marks"):
            add(strip, "card", type=kind)
        top = add(cards, "edge", name="top")
        for kind in ("columns", "rows", "title"):
            add(add(top, "strip", size=31 if kind == "title" else 2147483647),
                "card", type=kind)
        add(window, "simple-id", uuid=guid("window:" + title))
    window = add(windows, "window", **{
        "class": "dashboard", "name": board_name, "maximized": "true"
    })
    vp = add(window, "viewpoints")
    for title, *_ in VIEWS:
        add(vp, "viewpoint", name=title)
    add(window, "active", id=2)
    add(window, "simple-id", uuid=guid("dashboard-window"))
    E.indent(root, space="  ")
    xml = E.tostring(root, encoding="utf-8", xml_declaration=True)
    parsed = E.fromstring(xml)
    if len(parsed.findall("./worksheets/worksheet")) != 4:
        raise AssertionError("Expected four real-data worksheets")
    return xml


def build(source: Path, manifest: Path, report: Path, out: Path) -> Path:
    csv_bytes, snapshot = validated_records(source, manifest, report)
    twb = native_xml()
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(NAME, twb)
        archive.writestr(f"{FOLDER}/{DATA_FILE}", csv_bytes)
        archive.writestr(f"{FOLDER}/SOURCE.txt", (
            "Contains information licensed under the Open Government Licence - Toronto.\n"
            f"Source: {snapshot['meta']['source']}\n"
            f"Original raw CSV SHA256: {snapshot['meta']['source_sha256']}\n"
            "2025-01-01 through 2025-12-10: original TTC incident logs (not wait times).\n"
        ))
    with zipfile.ZipFile(out) as archive:
        if archive.testzip() is not None:
            raise ValueError("Corrupted Tableau package")
        rows = list(csv.DictReader(io.StringIO(
            archive.read(f"{FOLDER}/{DATA_FILE}").decode("utf-8")
        )))
        if len(rows) != snapshot["summary"]["recorded_incidents"]:
            raise ValueError("TWBX packaged event count mismatch")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--source-meta", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(build(a.source, a.source_meta, a.report, a.out))
