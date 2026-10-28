Attribute VB_Name = "CommuteIQReport"
Option Explicit

' Import into Excel VBA editor. Requires workbook sheets:
' Dashboard, validation_result and recommendation_event.
' Table data should be imported via Data > Get Data (CSV), with first row as headers.
' This macro refreshes workbook connections and saves the Dashboard sheet as PDF.
' Excel desktop for Windows/Mac; review output path before running.

Public Sub RefreshAndExportDashboard()
    Dim dest As String
    Dim folder As String
    Dim sheetToExport As Worksheet
    On Error GoTo HandleError

    Set sheetToExport = ThisWorkbook.Worksheets("Dashboard")
    ThisWorkbook.RefreshAll
    Application.CalculateUntilAsyncQueriesDone
    folder = ThisWorkbook.Path
    If Len(folder) = 0 Then
        MsgBox "Save the workbook before exporting.", vbExclamation
        Exit Sub
    End If
    dest = folder & Application.PathSeparator & "CommuteIQ_Operations_Report.pdf"
    sheetToExport.ExportAsFixedFormat Type:=xlTypePDF, Filename:=dest, Quality:=xlQualityStandard
    MsgBox "Report saved: " & dest, vbInformation
    Exit Sub
HandleError:
    MsgBox "Report export failed: " & Err.Description, vbCritical
End Sub
