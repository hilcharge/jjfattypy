'-------------------------------------------------------------------
' Convert Excel data to tsv format!
'-------------------------------------------------------------------
Option Explicit
' On Error Resume Next

' �ϐ��̐錾

Dim Msg
Dim objExcel
Dim targetSheetNum
Dim args, arg
Dim pCnt

'�Ώۂ͂P�߂̃V�[�g
targetSheetNum = 1
' �J�n����

'Msg = MsgBox("AMI�����F��EXCEL�t�@�C����JSON�p�����[�^�ɕϊ����܂��B" & vbCrLf _
'		& "�Ώۂ� xls�܂���xlsx�t�@�C���ł��B", vbYesNo, "��낵���ł����H")
'If Msg = vbNo Then
'    MsgBox "�����𒆎~���܂�", vbOkOnly, "�������~"
'    WScript.Quit
'End If

Set args = WScript.Arguments

' �J�����g�t�H���_��Excel�t�@�C����1������
' Excel���ǂ����̓t�@�C������ ".xls" �ŏI��邩�ǂ����Ŕ��f
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
'	MsgBox "�ϊ��I�����܂���",vbOkOnly, "��������"
'Else
'	MsgBox "�ϊ��Ώۃt�@�C���͂���܂���ł���",vbOkOnly, "��������"
'End If


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' ExcelToTSV
'  - Excel�̋@�\���g����Excel��TSV�ɕϊ�
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Sub ExcelToJson(objExcel, fullPathFileName, targetSheetNum)
    Dim xlSheet
    Dim WshShell
    Dim tsvFileName
    Dim colNum
	Dim fso
    Dim kLen	'�g���q�̒���
    Dim SelfPath '���g�̃p�X
	Dim objFileSys
    Dim FullCmd


    objExcel.DisplayAlerts = False
    objExcel.Workbooks.Open(fullPathFileName)
    Set xlSheet = objExcel.Worksheets(targetSheetNum)

'�ۑ�����
    kLen = Len(Mid(fullPathFileName, InstrRev(fullPathFileName, ".") + 1) ) + 1
    tsvFileName = Left(fullPathFileName, Len(fullPathFileName) - kLen) + ".txt"
    ' �s�r�u�ŕۑ�����ɂ� SaveAs ��2�ڂ̈����� 42 ���w��
    xlSheet.SaveAs tsvFileName, 42
	'xlSheet.SaveAs tsvFileName, 42,,,,,,,,,,1200
    objExcel.Workbooks.Close


End Sub
