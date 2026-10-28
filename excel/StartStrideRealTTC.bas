Attribute VB_Name = "StartStrideRealTTC"
Option Explicit

' STARTSTRIDE | Authentic TTC 2025 Streetcar Incident Reporting
' Excel for Microsoft 365 for Mac / Windows. No ActiveX, no COM APIs.
' Import this module into the supplied five-sheet, real-data workbook.
' The 2025 snapshot is frozen: Jan 1 to Dec 10, 2025.
' This module checks its documented source SHA256 and reconciles aggregates.
' It does NOT independently hash the source CSV or prove rider wait times.

Private Const VERIFIED_CSV_SHA256 As String = "eb73f629ea3bdbca0dbdb17f1215b930dadb9ee78885b6a4c871c9fc3b1d38c3"
Private Const VERIFIED_SOURCE As String = "https://pages.scinet.utoronto.ca/~afedosee/ttc-streetcar-delay-data-2014-2025.zip"
Private Const EXPECTED_SOURCE_ROWS As Long = 10903
Private Const EXPECTED_INCIDENTS As Long = 10744
Private Const EXPECTED_POSITIVE As Long = 8377
Private Const EXPECTED_EXCLUDED As Long = 159
Private Const EXPECTED_MINUTES As Double = 203665#
Private Const TOLERANCE As Double = 0.001

Private Type TTCTotals
    Incidents As Double
    Positive As Double
    Minutes As Double
    Labels As Long
End Type

' Run this to validate the source and save a QA record inside the workbook.
Public Sub RunStartStrideAudit()
    Dim summary As TTCTotals
    On Error GoTo Fail
    ValidateAll summary
    WriteAudit summary
    MsgBox "PASS - StartStride 2025 TTC data reconciled." & vbCrLf & _
           "Logged incidents: " & Format$(summary.Incidents, "#,##0") & vbCrLf & _
           "Positive-delay incidents: " & Format$(summary.Positive, "#,##0") & vbCrLf & _
           "Recorded incident delay minutes: " & Format$(summary.Minutes, "#,##0") & vbCrLf & _
           "See the QA_Audit sheet and save your workbook.", vbInformation, "StartStride QA"
    Exit Sub
Fail:
    MsgBox "FAIL - No report exported or data modified." & vbCrLf & Err.Description, _
           vbCritical, "StartStride QA"
End Sub

' Run this to validate the real data, log QA, and export the Dashboard to PDF.
Public Sub ExportStartStridePDF()
    Dim summary As TTCTotals
    Dim dashboard As Worksheet
    Dim audit As Worksheet
    Dim folder As String
    Dim slash As String
    Dim outputName As String
    Dim destination As String
    On Error GoTo Fail

    ValidateAll summary
    folder = ThisWorkbook.Path
    RequireTrue Len(folder) > 0, "Save the workbook as .xlsm in a LOCAL folder first."
    RequireTrue LCase$(Left$(folder, 4)) <> "http", _
                "Please save a local .xlsm copy rather than exporting from a web URL."
    slash = Application.PathSeparator
    If InStr(folder, "/") > 0 Then slash = "/"  ' Excel for Mac POSIX path
    If Right$(folder, 1) = slash Then slash = ""

    Set dashboard = ThisWorkbook.Worksheets("Dashboard")
    Set audit = WriteAudit(summary)
    dashboard.Calculate
    ' Some Excel for Mac printer setups reject PageSetup; PDF export still runs.
    On Error Resume Next
    With dashboard.PageSetup
        .PrintArea = "$A$1:$T$38"
        .Orientation = xlLandscape
        .Zoom = False
        .FitToPagesWide = 1
        .FitToPagesTall = 1
    End With
    Err.Clear
    On Error GoTo Fail

    outputName = "StartStride_TTC_2025_Audit_" & Format$(Now, "yyyymmdd_hhnnss") & ".pdf"
    destination = folder & slash & outputName
    dashboard.ExportAsFixedFormat Type:=xlTypePDF, _
                                  Filename:=destination, _
                                  Quality:=xlQualityStandard, _
                                  IncludeDocProperties:=True, _
                                  IgnorePrintAreas:=False, _
                                  OpenAfterPublish:=False
    audit.Range("A18").Value = "Most recent exported PDF"
    audit.Range("B18").Value = outputName
    audit.Range("A19").Value = "Exported at (local time)"
    audit.Range("B19").Value = Now
    audit.Range("B19").NumberFormat = "yyyy-mm-dd hh:mm:ss"
    MsgBox "StartStride PDF exported successfully:" & vbCrLf & destination & vbCrLf & _
           "QA passed. Save the .xlsm workbook to retain its QA_Audit sheet.", _
           vbInformation, "StartStride"
    Exit Sub
Fail:
    MsgBox "PDF NOT exported." & vbCrLf & Err.Description, _
           vbCritical, "StartStride"
End Sub

' Backward-compatible name used in the original StopStride module.
Public Sub VerifyRealTTCAndExport()
    ExportStartStridePDF
End Sub

' Installs two Form Control buttons in an Automation sheet. Form controls,
' unlike ActiveX buttons, are supported in desktop Excel for Mac.
Public Sub InstallStartStrideButtons()
    Dim panel As Worksheet
    Dim shape As Shape
    Dim item As Shape
    On Error GoTo Fail
    Set panel = GetOrCreateSheet("Automation")
    panel.Range("A1:F12").Clear
    panel.Columns("A").ColumnWidth = 4
    panel.Columns("B").ColumnWidth = 40
    panel.Columns("C:F").ColumnWidth = 14
    panel.Range("B2").Value = "STARTSTRIDE  |  REPORT AUTOMATION"
    panel.Range("B2").Font.Bold = True
    panel.Range("B2").Font.Size = 16
    panel.Range("B4").Value = "01   Validate TTC historical source + aggregates"
    panel.Range("B7").Value = "02   Export a verified Dashboard PDF"
    panel.Range("B10").Value = "Only actual 2025 TTC incident logs. Not live arrivals or rider delays."
    panel.Range("B10").Font.Italic = True
    For Each item In panel.Shapes
        If item.Name = "StartStrideAuditButton" Or item.Name = "StartStridePDFButton" Then
            item.Delete
        End If
    Next item

    Set shape = panel.Shapes.AddFormControl(xlButtonControl, 32, 132, 250, 35)
    shape.Name = "StartStrideAuditButton"
    shape.TextFrame.Characters.Text = "Run Source & Data Audit"
    shape.OnAction = "'" & ThisWorkbook.Name & "'!RunStartStrideAudit"

    Set shape = panel.Shapes.AddFormControl(xlButtonControl, 32, 214, 250, 35)
    shape.Name = "StartStridePDFButton"
    shape.TextFrame.Characters.Text = "Validate and Export PDF"
    shape.OnAction = "'" & ThisWorkbook.Name & "'!ExportStartStridePDF"

    panel.Activate
    MsgBox "Two StartStride automation buttons added. Save your .xlsm file.", _
           vbInformation, "StartStride"
    Exit Sub
Fail:
    MsgBox "Could not install buttons: " & Err.Description & vbCrLf & _
           "You can run the macros via Developer > Macros instead.", _
           vbExclamation, "StartStride"
End Sub

Private Sub ValidateAll(ByRef checked As TTCTotals)
    Dim byRoute As TTCTotals
    Dim byMonth As TTCTotals
    Dim byHour As TTCTotals
    Dim dashboard As Worksheet
    Dim provenance As Worksheet

    Set dashboard = ThisWorkbook.Worksheets("Dashboard")
    Set provenance = ThisWorkbook.Worksheets("Provenance")
    CheckProvenance provenance
    CheckTable ThisWorkbook.Worksheets("Route_Analysis"), "route", 86, byRoute
    CheckTable ThisWorkbook.Worksheets("Monthly"), "month", 12, byMonth
    CheckTable ThisWorkbook.Worksheets("Hourly"), "hour", 24, byHour

    RequireTrue EqualTotals(byRoute, byMonth), _
       "Route and monthly tables disagree (counts, positive delays or minutes)."
    RequireTrue EqualTotals(byRoute, byHour), _
       "Route and hourly tables disagree (counts, positive delays or minutes)."
    RequireTrue Abs(byRoute.Incidents - EXPECTED_INCIDENTS) < TOLERANCE, _
       "Logged incident count differs from the verified 2025 TTC snapshot."
    RequireTrue Abs(byRoute.Positive - EXPECTED_POSITIVE) < TOLERANCE, _
       "Positive delay count differs from the verified 2025 TTC snapshot."
    RequireTrue Abs(byRoute.Minutes - EXPECTED_MINUTES) < TOLERANCE, _
       "Recorded delay minutes differ from the verified 2025 TTC snapshot."

    dashboard.Calculate
    RequireTrue IsNumeric(dashboard.Range("A6").Value2), "Dashboard A6 is not numeric."
    RequireTrue IsNumeric(dashboard.Range("D6").Value2), "Dashboard D6 is not numeric."
    RequireTrue IsNumeric(dashboard.Range("G6").Value2), "Dashboard G6 is not numeric."
    RequireTrue Abs(CDbl(dashboard.Range("A6").Value2) - byRoute.Incidents) < TOLERANCE, _
       "Dashboard logged incident KPI differs from source tables."
    RequireTrue Abs(CDbl(dashboard.Range("D6").Value2) - byRoute.Positive) < TOLERANCE, _
       "Dashboard positive-delay KPI differs from source tables."
    RequireTrue Abs(CDbl(dashboard.Range("G6").Value2) - byRoute.Minutes) < TOLERANCE, _
       "Dashboard recorded-delay-minute KPI differs from source tables."
    checked = byRoute
End Sub

Private Sub CheckProvenance(ByVal sheet As Worksheet)
    RequireTrue CStr(sheet.Range("A7").Value2) = "Raw CSV SHA256", _
                "Provenance!A7 checksum field is missing."
    RequireTrue LCase$(Trim$(CStr(sheet.Range("B7").Value2))) = VERIFIED_CSV_SHA256, _
                "Provenance checksum does not match the actual 2025 source CSV."
    RequireTrue Trim$(CStr(sheet.Range("B4").Value2)) = VERIFIED_SOURCE, _
                "Archive source URL differs from the verified TTC source."
    RequireTrue Trim$(CStr(sheet.Range("B6").Value2)) = "2025-01-01 to 2025-12-10", _
                "Data coverage has changed; refresh the validation contract first."
    RequireTrue IsNumeric(sheet.Range("B8").Value2), "Missing raw CSV row count."
    RequireTrue IsNumeric(sheet.Range("B9").Value2), "Missing retained row count."
    RequireTrue IsNumeric(sheet.Range("B10").Value2), "Missing excluded row count."
    RequireTrue CDbl(sheet.Range("B8").Value2) = EXPECTED_SOURCE_ROWS, _
                "Raw TTC source row count differs from original."
    RequireTrue CDbl(sheet.Range("B9").Value2) = EXPECTED_INCIDENTS, _
                "Validated row count differs from 2025 snapshot."
    RequireTrue CDbl(sheet.Range("B10").Value2) = EXPECTED_EXCLUDED, _
                "Excluded row count differs from snapshot."
    RequireTrue CDbl(sheet.Range("B8").Value2) = _
                CDbl(sheet.Range("B9").Value2) + CDbl(sheet.Range("B10").Value2), _
                "Source row-count accounting does not reconcile."
End Sub

Private Sub CheckTable(ByVal sheet As Worksheet, ByVal kind As String, _
                       ByVal expectedLabels As Long, ByRef totals As TTCTotals)
    Dim lastRow As Long
    Dim i As Long
    Dim j As Long
    Dim label As String
    Dim incidents As Double
    Dim positive As Double
    Dim minutes As Double
    Dim hourValue As Long
    Dim monthNumber As Long
    lastRow = sheet.Cells(sheet.Rows.Count, 1).End(xlUp).Row
    RequireTrue lastRow = expectedLabels + 1, _
       sheet.Name & " does not contain the expected number of source labels."
    totals.Incidents = 0
    totals.Positive = 0
    totals.Minutes = 0
    totals.Labels = expectedLabels
    For i = 2 To lastRow
        RequireTrue Not IsError(sheet.Cells(i, 1).Value), sheet.Name & " has an invalid label."
        label = Trim$(CStr(sheet.Cells(i, 1).Value2))
        RequireTrue Len(label) > 0, sheet.Name & " has a blank label on row " & i
        For j = 2 To i - 1
            RequireTrue StrComp(label, Trim$(CStr(sheet.Cells(j, 1).Value2)), _
                                vbTextCompare) <> 0, _
                       sheet.Name & " has duplicated label: " & label
        Next j
        If kind = "hour" Then
            RequireTrue IsNumeric(sheet.Cells(i, 1).Value2), "Non-numeric hour: " & label
            hourValue = CLng(sheet.Cells(i, 1).Value2)
            RequireTrue hourValue >= 0 And hourValue <= 23, "Invalid hour: " & label
        ElseIf kind = "month" Then
            RequireTrue label Like "####-##", "Invalid YYYY-MM month: " & label
            RequireTrue Left$(label, 4) = "2025", "Non-2025 month: " & label
            monthNumber = CLng(Right$(label, 2))
            RequireTrue monthNumber >= 1 And monthNumber <= 12, "Invalid month: " & label
        End If
        RequireTrue IsNumeric(sheet.Cells(i, 2).Value2), sheet.Name & " B" & i & " not numeric."
        RequireTrue IsNumeric(sheet.Cells(i, 3).Value2), sheet.Name & " C" & i & " not numeric."
        RequireTrue IsNumeric(sheet.Cells(i, 4).Value2), sheet.Name & " D" & i & " not numeric."
        incidents = CDbl(sheet.Cells(i, 2).Value2)
        positive = CDbl(sheet.Cells(i, 3).Value2)
        minutes = CDbl(sheet.Cells(i, 4).Value2)
        RequireTrue incidents >= 0 And positive >= 0 And minutes >= 0, _
                    "Negative numbers on " & sheet.Name & " row " & i
        RequireTrue Abs(incidents - Fix(incidents)) < TOLERANCE, "Fractional incidents."
        RequireTrue Abs(positive - Fix(positive)) < TOLERANCE, "Fractional positive count."
        RequireTrue positive <= incidents, "Positive incidents exceed total on row " & i
        totals.Incidents = totals.Incidents + incidents
        totals.Positive = totals.Positive + positive
        totals.Minutes = totals.Minutes + minutes
    Next i
End Sub

Private Function EqualTotals(ByRef a As TTCTotals, ByRef b As TTCTotals) As Boolean
    EqualTotals = Abs(a.Incidents - b.Incidents) < TOLERANCE And _
                  Abs(a.Positive - b.Positive) < TOLERANCE And _
                  Abs(a.Minutes - b.Minutes) < TOLERANCE
End Function

Private Sub RequireTrue(ByVal condition As Boolean, ByVal explanation As String)
    If Not condition Then Err.Raise vbObjectError + 2111, "StartStrideRealTTC", explanation
End Sub

Private Function GetOrCreateSheet(ByVal name As String) As Worksheet
    On Error Resume Next
    Set GetOrCreateSheet = ThisWorkbook.Worksheets(name)
    On Error GoTo 0
    If GetOrCreateSheet Is Nothing Then
        Set GetOrCreateSheet = ThisWorkbook.Worksheets.Add( _
             After:=ThisWorkbook.Worksheets(ThisWorkbook.Worksheets.Count))
        GetOrCreateSheet.Name = name
    End If
End Function

Private Function WriteAudit(ByRef totals As TTCTotals) As Worksheet
    Dim sheet As Worksheet
    Set sheet = GetOrCreateSheet("QA_Audit")
    sheet.Range("A1:D20").Clear
    sheet.Range("A1:D1").Merge
    sheet.Range("A1").Value = "STARTSTRIDE  |  VERIFIED TTC 2025 SOURCE AUDIT"
    With sheet.Range("A1:D1")
        .Interior.Color = RGB(18, 36, 57)
        .Font.Color = RGB(255, 255, 255)
        .Font.Bold = True
        .Font.Size = 14
        .RowHeight = 34
    End With
    sheet.Range("A3").Value = "Audit outcome"
    sheet.Range("B3").Value = "PASS"
    sheet.Range("B3").Interior.Color = RGB(208, 242, 220)
    sheet.Range("B3").Font.Color = RGB(20, 106, 65)
    sheet.Range("A4").Value = "Checked at (local time)"
    sheet.Range("B4").Value = Now
    sheet.Range("B4").NumberFormat = "yyyy-mm-dd hh:mm:ss"
    sheet.Range("A5").Value = "Logged TTC incidents"
    sheet.Range("B5").Value = totals.Incidents
    sheet.Range("A6").Value = "Positive-delay incidents"
    sheet.Range("B6").Value = totals.Positive
    sheet.Range("A7").Value = "Recorded service-delay minutes"
    sheet.Range("B7").Value = totals.Minutes
    sheet.Range("A8").Value = "Distinct raw route labels"
    sheet.Range("B8").Value = totals.Labels
    sheet.Range("A9").Value = "Months checked"
    sheet.Range("B9").Value = 12
    sheet.Range("A10").Value = "Hours checked"
    sheet.Range("B10").Value = 24
    sheet.Range("A11").Value = "Source SHA256 (documented)"
    sheet.Range("B11").Value = VERIFIED_CSV_SHA256
    sheet.Range("A12").Value = "Data coverage"
    sheet.Range("B12").Value = "2025-01-01 to 2025-12-10"
    sheet.Range("A13").Value = "Route, monthly, hourly totals"
    sheet.Range("B13").Value = "MATCH"
    sheet.Range("A14").Value = "Dashboard KPI totals"
    sheet.Range("B14").Value = "MATCH"
    sheet.Range("A15").Value = "Interpretation"
    sheet.Range("B15").Value = "Reported incidents, NOT individual rider or streetcar lateness rates."
    sheet.Range("A16").Value = "Validation caveat"
    sheet.Range("B16").Value = "Checks stored checksum and aggregates; does not rehash original CSV."
    sheet.Columns("A").ColumnWidth = 37
    sheet.Columns("B").ColumnWidth = 79
    sheet.Columns("C:D").ColumnWidth = 12
    sheet.Range("B5:B10").NumberFormat = "#,##0"
    sheet.Range("B15:B16").WrapText = True
    sheet.Rows("15:16").RowHeight = 34
    Set WriteAudit = sheet
End Function
