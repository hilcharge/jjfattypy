'-------------------------------------------------------------------
' Convert Excel data to tsv format!
'-------------------------------------------------------------------
Option Explicit
' On Error Resume Next

' 変数の宣言

Dim Msg
Dim objExcel
Dim targetSheetNum
Dim args, arg
Dim pCnt

'対象は１つめのシート
targetSheetNum = 1
' 開始処理

'Msg = MsgBox("AMI音声認識EXCELファイルをJSONパラメータに変換します。" & vbCrLf _
'		& "対象は xlsまたはxlsxファイルです。", vbYesNo, "よろしいですか？")
'If Msg = vbNo Then
'    MsgBox "処理を中止します", vbOkOnly, "処理中止"
'    WScript.Quit
'End If

Set args = WScript.Arguments

' カレントフォルダのExcelファイルを1つずつ処理
' Excelかどうかはファイル名が ".xls" で終わるかどうかで判断
Set objExcel  = CreateObject("Excel.Application")
pCnt = 0

For Each arg In args
	If Right(arg, 3) = "xls" OR Right(arg, 4) = "xlsx" OR Right(arg,4) = "xlsm" Then
    	ExcelToJson objExcel, arg, targetSheetNum
		pCnt = pCnt + 1
	End If
Next

Set objExcel = Nothing

'If pCnt > 0 Then
'	MsgBox "変換終了しました",vbOkOnly, "処理完了"
'Else
'	MsgBox "変換対象ファイルはありませんでした",vbOkOnly, "処理完了"
'End If


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' ExcelToTSV
'  - Excelの機能を使ってExcelをTSVに変換
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Sub ExcelToJson(objExcel, fullPathFileName, targetSheetNum)
    Dim xlSheet
    Dim WshShell
    Dim tsvFileName
    Dim colNum
	Dim fso
    Dim kLen	'拡張子の長さ
    Dim SelfPath '自身のパス
	Dim objFileSys
    Dim FullCmd


    objExcel.DisplayAlerts = False
    objExcel.Workbooks.Open(fullPathFileName)
    Set xlSheet = objExcel.Worksheets(targetSheetNum)

'保存する
    kLen = Len(Mid(fullPathFileName, InstrRev(fullPathFileName, ".") + 1) ) + 1
    tsvFileName = Left(fullPathFileName, Len(fullPathFileName) - kLen) + ".txt"
    ' ＴＳＶで保存するには SaveAs の2つ目の引数で 42 を指定
    xlSheet.SaveAs tsvFileName, 42
	'xlSheet.SaveAs tsvFileName, 42,,,,,,,,,,1200
    objExcel.Workbooks.Close


End Sub
