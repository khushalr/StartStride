# StartStride — Real TTC streetcar Excel and VBA reporting

The canonical macro source is **StartStrideRealTTC.bas**. It supersedes the earlier StopStrideRealTTC.bas prototype. This module operates on the verified historical 2025 TTC streetcar incident data. It uses no synthetic travel or arrival records.

## Mac setup and operation

1. Open the provided StartStride_Real_TTC_2025_VBA_Starter.xlsx in desktop Microsoft Excel.
2. Enable Developer under Excel > Settings / Preferences > Ribbon & Toolbar.
3. Developer > Visual Basic > File > Import File; choose StartStrideRealTTC.bas.
4. Save As > Excel Macro-Enabled Workbook (.xlsm) in a local folder. A normal .xlsx file cannot store macros.
5. Run **InstallStartStrideButtons** under Developer > Macros. This adds two Excel Form Control buttons to a new Automation sheet; alternatively use the Macros menu to run routines directly.
6. Run **RunStartStrideAudit**. It writes an auditable QA_Audit worksheet if all checks pass.
7. Run **ExportStartStridePDF**. It reruns validation and saves the Dashboard as a timestamped PDF alongside the local .xlsm workbook. Save the workbook again to keep its QA log.

## Source and audit contract

The workbook includes Dashboard, Route_Analysis, Monthly, Hourly, Provenance and a VBA_Setup guide sheet. It is based on the City of Toronto TTC streetcar incident records, archived by University of Toronto SciNet: https://pages.scinet.utoronto.ca/~afedosee/ttc-streetcar-delay-data-2014-2025.zip .

The reported 2025 incident source ends **2025-12-10**. Its original CSV SHA256 is eb73f629ea3bdbca0dbdb17f1215b930dadb9ee78885b6a4c871c9fc3b1d38c3.

The VBA validates that the stored source checksum, URL, date range and accounting are correct. It checks for exactly 10,744 retained incidents, 8,377 positive-delay incident records, 203,665 minutes of recorded incident service delays, 86 raw route labels, 12 months and 24 hours. It checks labels and data types, nonnegative and integer counts, cross-table sums, and dashboard KPIs before exporting.

**The VBA checks the workbook's stored checksum; it does not independently rehash the original source CSV bytes.** The workbook stores aggregate data, not the raw CSV.

TTC incidents are NOT passenger journey delays, on-time performance rates, or actual streetcar ETAs. December 2025 is incomplete. These historical figures cannot determine whether a rider should wait or walk.

## Verification status

- Excel workbook summaries, formulas and charts programmatically checked.
- Static Python tests check VBA module constants against the real version-controlled TTC JSON and CSV exports.
- **Excel VBA runtime, buttons and PDF export cannot be validated in this environment. They must be tested in desktop Excel for Mac before claiming fully working automation.**

Older CommuteIQReport.bas relates to a synthetic prototype and must not be used for real-data reporting. This is an independent analysis, licensed with attribution under the Open Government Licence – Toronto, not endorsed by the TTC.
