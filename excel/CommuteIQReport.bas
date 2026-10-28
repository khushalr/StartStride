Attribute VB_Name = "CommuteIQReport"
Option Explicit

' CommuteIQ Excel reporting prototype.
' Workbook should contain:
'   - Dashboard (may be empty)
'   - validation_result (headers from exported CSV)
'   - recommendation_event (headers from exported CSV)
' Import CSV files through Excel Data > From Text/CSV and name the sheets as above.
' IMPORTANT: RefreshAll can be asynchronous for some connections. Verify the
' underlying imported tables finished refreshing before treating the PDF as current.

Private Function HeaderColumn(ByVal ws As Worksheet, ByVal name As String) As Long
    Dim header As Range
    Set header = ws.Rows(1).Find(What:=name, LookIn:=xlValues, LookAt:=xlWhole)
    If header Is Nothing Then Err.Raise vbObjectError + 1201, , _
        "Missing column '" & name & "' on sheet " & ws.Name
    HeaderColumn = header.Column
End Function

Public Sub BuildOperationsSummary()
    Dim summary As Worksheet, qa As Worksheet, rec As Worksheet
    Dim qaLast As Long, recLast As Long, i As Long
    Dim statusCol As Long, actionCol As Long, stepsCol As Long, originCol As Long
    Dim totalRules As Long, failedRules As Long, walkCount As Long, waitCount As Long
    Dim potentialSteps As Double, demoEvents As Long

    Set summary = ThisWorkbook.Worksheets("Dashboard")
    Set qa = ThisWorkbook.Worksheets("validation_result")
    Set rec = ThisWorkbook.Worksheets("recommendation_event")
    statusCol = HeaderColumn(qa, "status")
    actionCol = HeaderColumn(rec, "action")
    stepsCol = HeaderColumn(rec, "expected_steps")
    originCol = HeaderColumn(rec, "data_origin")

    qaLast = qa.Cells(qa.Rows.Count, statusCol).End(xlUp).Row
    recLast = rec.Cells(rec.Rows.Count, actionCol).End(xlUp).Row

    For i = 2 To qaLast
        If Len(Trim$(CStr(qa.Cells(i, statusCol).Value))) > 0 Then
            totalRules = totalRules + 1
            If UCase$(Trim$(CStr(qa.Cells(i, statusCol).Value))) = "FAIL" Then
                failedRules = failedRules + 1
            End If
        End If
    Next i

    For i = 2 To recLast
        Select Case UCase$(Trim$(CStr(rec.Cells(i, actionCol).Value)))
            Case "WALK"
                walkCount = walkCount + 1
                If IsNumeric(rec.Cells(i, stepsCol).Value) Then
                    potentialSteps = potentialSteps + CDbl(rec.Cells(i, stepsCol).Value)
                End If
            Case "WAIT"
                waitCount = waitCount + 1
        End Select
        If UCase$(Trim$(CStr(rec.Cells(i, originCol).Value))) = "DEMO" Then
            demoEvents = demoEvents + 1
        End If
    Next i

    summary.Range("A1:B9").ClearContents
    summary.Range("A1").Value = "CommuteIQ | QA and Rider Recommendation Summary"
    summary.Range("A2").Value = "Generated at"
    summary.Range("B2").Value = Format$(Now, "yyyy-mm-dd hh:nn")
    summary.Range("A3").Value = "QA rules checked"
    summary.Range("B3").Value = totalRules
    summary.Range("A4").Value = "Failed QA rules"
    summary.Range("B4").Value = failedRules
    summary.Range("A5").Value = "QA pass rate"
    If totalRules > 0 Then summary.Range("B5").Value = (totalRules - failedRules) / totalRules
    summary.Range("B5").NumberFormat = "0.0%"
    summary.Range("A6").Value = "WALK recommendations"
    summary.Range("B6").Value = walkCount
    summary.Range("A7").Value = "WAIT recommendations"
    summary.Range("B7").Value = waitCount
    summary.Range("A8").Value = "Potential steps (NOT actual steps)"
    summary.Range("B8").Value = potentialSteps
    summary.Range("A9").Value = "Synthetic demo events"
    summary.Range("B9").Value = demoEvents
    summary.Columns("A:B").AutoFit
    summary.Range("A1").Font.Bold = True
    summary.PageSetup.PrintArea = "$A$1:$B$9"
End Sub

Public Sub RefreshAndExportDashboard()
    Dim dest As String, folder As String
    On Error GoTo HandleError

    If Len(ThisWorkbook.Path) = 0 Then
        MsgBox "Save this .xlsm workbook before exporting.", vbExclamation
        Exit Sub
    End If
    ThisWorkbook.RefreshAll
    ' For connections that refresh in the background, wait for the external
    ' refresh to finish and run this macro again before distributing the PDF.
    Application.Calculate
    BuildOperationsSummary

    folder = ThisWorkbook.Path
    dest = folder & Application.PathSeparator & "CommuteIQ_Operations_Report.pdf"
    ThisWorkbook.Worksheets("Dashboard").ExportAsFixedFormat _
        Type:=xlTypePDF, Filename:=dest, Quality:=xlQualityStandard

    MsgBox "Report saved: " & dest & vbCrLf & _
        "Confirm source-table refresh and DEMO/LIVE labels before sharing.", vbInformation
    Exit Sub
HandleError:
    MsgBox "CommuteIQ report failed: " & Err.Description, vbCritical
End Sub
