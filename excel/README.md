# Excel operations dashboard and VBA reporting

This folder contains `CommuteIQReport.bas`, an Excel desktop VBA module. A companion, formula-driven `.xlsx` portfolio demo is generated separately and must be reviewed in Excel before it is added to a public release.

**Important:** The report fixture contains **synthetic** examples (not live TTC operations or rider activity). The product's working brand may change; the package filename does not create a trademark claim.

## Workbook contract

The operations workbook needs these exact worksheet names:

| Sheet | Purpose |
|---|---|
| `Dashboard` | KPI report, cells A1:B9, plus optional visualizations to the right |
| `validation_result` | QA results, with first-row headings `rule_id`, `status`, `affected_records` and `data_origin` |
| `recommendation_event` | Decisions, with first-row headings `route_id`, `action`, `expected_steps`, `data_origin` |
| `Route_Summary` | Excel formula-driven route KPIs and chart source |
| `Read_Me` | Definitions, limitations and usage |

Columns **can be rearranged** as long as header labels match; VBA searches the first row by name. The workbook also provides explicit DEMO provenance.

## What the VBA actually computes

`BuildOperationsSummary` reads worksheet rows and calculates:

- QA rule count and count of failed rules.
- Rule pass rate.
- Number of WALK and WAIT recommendations.
- Sum of potential steps **only** for WALK recommendations.
- Number of DEMO-labelled recommendation events.

`RefreshAndExportDashboard` requests source refresh, recalculates this summary, and exports the `Dashboard` sheet to PDF alongside the workbook.

The VBA is **source code, not a pre-enabled macro workbook**. It has not been executed and validated in Excel for Mac or Excel for Windows. External data connections may refresh asynchronously, so verify the source sheets have finished refreshing before sharing the PDF.

## How to use this in desktop Excel

1. Open the companion `.xlsx` workbook and confirm the five sheet names and the DEMO banner.
2. Save As `Excel Macro-Enabled Workbook (.xlsm)` in a trusted local folder.
3. Open the Visual Basic Editor and import `CommuteIQReport.bas` as a module.
4. Run `BuildOperationsSummary` first and compare it with formula-driven KPIs.
5. Run `RefreshAndExportDashboard` and check that the PDF is readable and carries the synthetic-data warning.
6. Do not enable unknown macros from unsolicited spreadsheets; this module is open-source and should be reviewed before use.

### Expected results for the versioned synthetic fixture

| Metric | Expected |
|---|---:|
| GTFS QA rules | 16 |
| Failed rules | 3 |
| Rule pass rate | 81.25% |
| Simulated recommendation events | 36 |
| Suggested WALK | 15 |
| Suggested WAIT | 21 |
| Potential steps from WALK suggestions | 6,930 |
| Verified streetcar catches | 0 observations (unknown, **not zero catches**) |

## Next Excel engineering milestones

- Test and record the desktop Excel macro run (Mac and Windows compatibility).
- Create a source refresh mechanism tied to the SQL export.
- Add a sample PDF screenshot/artifact only after successful validation in Excel.
- Publish a verified macro-enabled workbook under Releases if appropriate.

## Licensing and safety

The project is an independent transit data science demo; it is not affiliated with or endorsed by the TTC. Synthetic movement recommendations are not safety instructions for a live street or a guarantee of boarding.
