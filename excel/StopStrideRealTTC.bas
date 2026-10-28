Attribute VB_Name = "StopStrideRealTTC"
Option Explicit

' STOPSTRIDE | Real TTC Streetcar Incident Reporting
' Import only into desktop Excel after reviewing this module.
' Target workbook has Dashboard, Route_Analysis, Monthly, Hourly and Provenance.
' Data must be original TTC data, not test fixtures.
' This module has NOT been executed inside Excel and requires desktop verification.

Public Sub VerifyRealTTCAndExport()
    Dim worksheetDash As Worksheet
    Dim worksheetRoutes As Worksheet
    Dim worksheetMonthly As Worksheet
    Dim worksheetProvenance As Worksheet
    Dim totalEvents As Double
    Dim totalPositive As Double
    Dim totalMinutes As Double
    Dim lastRoute As Long
    Dim lastMonth As Long
    Dim sourceSha As String
    Dim exportPath As String

    On Error GoTo HandleError

    Set worksheetDash = ThisWorkbook.Worksheets("Dashboard")
    Set worksheetRoutes = ThisWorkbook.Worksheets("Route_Analysis")
    Set worksheetMonthly = ThisWorkbook.Worksheets("Monthly")
    Set worksheetProvenance = ThisWorkbook.Worksheets("Provenance")

    If Len(ThisWorkbook.Path) = 0 Then
        Err.Raise vbObjectError + 1000, , "Save the workbook to a trusted local folder before exporting."
    End If

    ' Ensure source lineage is present.
    If CStr(worksheetProvenance.Range("A7").Value) <> "Raw CSV SHA256" Then
        Err.Raise vbObjectError + 1001, , "Missing source-checksum field on Provenance sheet."
    End If
    sourceSha = Trim$(CStr(worksheetProvenance.Range("B7").Value))
    If Len(sourceSha) <> 64 Then
        Err.Raise vbObjectError + 1002, , "Invalid SHA256 provenance (expected 64 characters)."
    End If

    lastRoute = worksheetRoutes.Cells(worksheetRoutes.Rows.Count, "A").End(xlUp).Row
    lastMonth = worksheetMonthly.Cells(worksheetMonthly.Rows.Count, "A").End(xlUp).Row
    If lastRoute < 2 Or lastMonth < 2 Then
        Err.Raise vbObjectError + 1003, , "No verified source tables available."
    End If

    totalEvents = Application.Sum(worksheetRoutes.Range("B2:B" & lastRoute))
    totalPositive = Application.Sum(worksheetRoutes.Range("C2:C" & lastRoute))
    totalMinutes = Application.Sum(worksheetRoutes.Range("D2:D" & lastRoute))

    ' Cross-check the monthly source against route totals.
    If Abs(Application.Sum(worksheetMonthly.Range("B2:B" & lastMonth)) - totalEvents) > 0.001 Then
        Err.Raise vbObjectError + 1004, , "Monthly and route source totals disagree. No report exported."
    End If
    If totalEvents <= 0 Or totalPositive > totalEvents Or totalMinutes < 0 Then
        Err.Raise vbObjectError + 1005, , "Source counts do not pass validation."
    End If

    worksheetDash.Calculate
    exportPath = ThisWorkbook.Path & Application.PathSeparator & "StopStride_Real_TTC_Report.pdf"

    worksheetDash.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:=exportPath, Quality:=xlQualityStandard, OpenAfterPublish:=False

    MsgBox "Report exported: " & exportPath & vbCrLf & _
        "Verified TTC logged incidents: " & Format(totalEvents, "#,##0") & vbCrLf & _
        "These are NOT per-trip reliability rates.", vbInformation
    Exit Sub
HandleError:
    MsgBox "Real TTC report NOT exported. " & Err.Description, vbCritical
End Sub
