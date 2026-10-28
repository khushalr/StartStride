# StopStride Excel/VBA analytics — REAL TTC streetcar records

**Use the validated TTC historical incident data in `dashboard/bi/`.** The earlier synthetic wait/walk reporting experiment is not a source for public claims.

## Excel workbook with real records

A five-sheet `.xlsx` portfolio workbook was generated from the archived original TTC 2025 CSV. Its sheets are:

- `Dashboard`: formula-driven logged-incident KPIs and route/month charts.
- `Route_Analysis`: all TTC reported route labels, actual incident counts, positive-delay counts and recorded minutes.
- `Monthly`: logged historical incident totals by month.
- `Hourly`: logged historical incident totals by recorded time of day.
- `Provenance`: verified source URL, SHA256 checksum, covered dates, excluded record count and methodological limitations.

Rebuild equivalent Excel tables from the version-controlled **real** `dashboard/bi/streetcar_*.csv` files. No fake data is needed. The corresponding source manifest is `dashboard/bi/SOURCE.json`.

## VBA reporting module

The relevant module is **`StopStrideRealTTC.bas`**. Import it into the Visual Basic Editor of a saved macro-enabled `.xlsm` copy of the real-data workbook.

`VerifyRealTTCAndExport` checks the source SHA256 cell, nonempty route/month data, total logged incidents reconciled across tables, and exports a formatted Dashboard PDF if those checks pass. It fails visibly when inputs are missing or inconsistent.

**VBA execution has not been validated in desktop Excel yet.** Review the source, test it in Excel and inspect the generated PDF before claiming operational automation.

The old `CommuteIQReport.bas` is historical prototype code for simulated recommendation events and is not appropriate for the verified real TTC incident workbook.

## Measurement notes

The unit of observation is a TTC-recorded incident, not an individual passenger journey or a particular streetcar trip. Route incident counts are not on-time performance rates.

Contains information licensed under the Open Government Licence – Toronto. StopStride is an independent research project, not affiliated with the TTC.
