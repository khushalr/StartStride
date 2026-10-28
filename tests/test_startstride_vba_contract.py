"""Static VBA checks; these do not execute VBA in Excel."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_startstride_module_links_to_verified_2025_ttc_snapshot():
    snapshot = json.loads((ROOT / "dashboard/real_data.json").read_text())
    bas = (ROOT / "excel/StartStrideRealTTC.bas").read_text()
    assert snapshot["meta"]["origin"] == "REAL"
    assert snapshot["meta"]["first_record"] == "2025-01-01"
    assert snapshot["meta"]["last_record"] == "2025-12-10"
    for key, val in {
        "VERIFIED_CSV_SHA256": snapshot["meta"]["source_sha256"],
        "VERIFIED_SOURCE": snapshot["meta"]["source"],
    }.items():
        assert f'{key} As String = "{val}"' in bas
    expected = {
        "EXPECTED_SOURCE_ROWS": snapshot["meta"]["rows_in_source"],
        "EXPECTED_INCIDENTS": snapshot["summary"]["recorded_incidents"],
        "EXPECTED_POSITIVE": snapshot["summary"]["positive_delay_incidents"],
        "EXPECTED_EXCLUDED": snapshot["meta"]["rows_dropped_invalid_or_before_2025"],
    }
    for key, val in expected.items():
        assert re.search(rf"\b{key}\s+As\s+Long\s*=\s*{val}\b", bas)
    assert re.search(
        rf"EXPECTED_MINUTES\s+As\s+Double\s*=\s*{int(snapshot['summary']['sum_recorded_delay_minutes'])}#",
        bas
    )
    assert snapshot["meta"]["rows_in_source"] == (
        snapshot["meta"]["rows_valid_2025_onward"]
        + snapshot["meta"]["rows_dropped_invalid_or_before_2025"]
    )


def test_mac_compatible_audit_and_pdf_macro_entrypoints_exist():
    bas = (ROOT / "excel/StartStrideRealTTC.bas").read_text()
    assert bas.startswith('Attribute VB_Name = "StartStrideRealTTC"')
    for name in ["RunStartStrideAudit", "ExportStartStridePDF",
                 "InstallStartStrideButtons", "VerifyRealTTCAndExport"]:
        assert f"Public Sub {name}()" in bas
    for token in ["Application.PathSeparator", "ExportAsFixedFormat",
                  "xlTypePDF", "QA_Audit", "Provenance",
                  "Route_Analysis", "Monthly", "Hourly", "Dashboard",
                  "Shapes.AddFormControl", "xlButtonControl"]:
        assert token in bas
    assert "CreateObject(" not in bas
    assert "Shell(" not in bas
    assert "MSForms." not in bas


def test_verified_bi_export_totals_match_original_snapshot():
    data = json.loads((ROOT / "dashboard/real_data.json").read_text())
    expected = data["summary"]
    for filename, minutes_name in [
        ("streetcar_routes.csv", "total_recorded_delay_minutes"),
        ("streetcar_monthly.csv", "recorded_delay_minutes"),
        ("streetcar_hourly.csv", "recorded_delay_minutes"),
    ]:
        with (ROOT / "dashboard/bi" / filename).open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert sum(int(r["recorded_incidents"]) for r in rows) == expected["recorded_incidents"]
        assert sum(int(r["positive_delay_incidents"]) for r in rows) == expected["positive_delay_incidents"]
        assert abs(sum(float(r[minutes_name]) for r in rows)
                   - expected["sum_recorded_delay_minutes"]) < 0.001
        if filename == "streetcar_routes.csv":
            assert len(rows) == expected["route_count"]
        elif filename == "streetcar_monthly.csv":
            assert len(rows) == 12
        else:
            assert len(rows) == 24
