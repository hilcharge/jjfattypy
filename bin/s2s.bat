@echo off
REM Usage: s2s T \\source\drive source\dir U \\dest\drive dest\dir

SET LOCAL_DEST_DIR=%USERPROFILE%\temp\transfer

IF "%~1"=="" GOTO USAGE
IF "%~2"=="" GOTO USAGE
IF "%~3"=="" GOTO USAGE
IF "%~4"=="" GOTO USAGE
IF "%~5"=="" GOTO USAGE
IF "%~6"=="" GOTO USAGE

echo Local storage: %LOCAL_DEST_DIR%

echo Source drive: %~1
SET SOURCE_DRIVE=%~1:
echo Source drive's target: %~2
SET SOURCE_SHARED_FOLDER=%~2
echo Source directory of copying: %~3
SET SOURCE_DIR=%SOURCE_DRIVE%\%~3
echo Destination drive: %~4
SET DEST_DRIVE=%~4:
echo Destination drive's target: %~5
SET DEST_SHARED_DIR=%~5
echo Destination folder: %~6
SET DEST_DIR=%DEST_DRIVE%\%~6

SET ORIG_DIR=%cd%
REM This could be changed to be based on command-line parameters eventually
SET SOURCEUSER=%USERNAME%
SET SOURCEDOMAIN=%USERDOMAIN%

SET DESTUSER=%USERNAME%
SET DESTDOMAIN=%USERDOMAIN%

SET EXCLUDES_FILE=excludes.txt


REM This is a script for copying files from a shared network drive which is not reliably connected onto a local machine
REM Then, it will copy the file onto a different server
REM It only uses the running users windows authetnication data, so no password is required **if the user is logged in**. Otherwise, this script will not work
REM To make it applicable 
REM To use, you should change all the following variables:
REM SOURCE_DRIVE,SOURCE_SHARED_FOLDER,SOURCE_DIR,LOCAL_DEST_DIR
REM DEST_DRIVE, DEST_SHARED_FOLDER, DEST_DIR
REM Explanation:
REM SOURCE_DRIVE is the device name for SOURCE_SHARED_FOLDER
REM SOURCE_DIR is the directory on the shared device, which should be copied from
REM LOCAL_DEST_DIR is the temporary folder, where files are stored before being copied onto the other server
REM DEST_DRIVE is the device name of the target
REM DEST_SHARED_DIR is the target of the dest_drive
REM DEST_DIR is the directory within the drive that is the ultimate target of the files to be copied

REM Send your updated code to Colin at hilchey@mail.nissan.co.jp

REM Source drive is the new device name, from which the files are being copied
REM source shared folder is the target of the mapped network device e.g. \\ami-server\db-snapshot

REM source_dir is the shared directory within the source_dir, or could be the same thing
REM The contents of this directory will be copied in their entirety onto your local machine

REM The DEST_DRIVE is the device name of the mapped directory of the 
REM The DEST_SHARED_DIR is the target of the destination drive, i.e. \\jk0cd001\共有フォルダ
REM DEST_DIR is the target directory of the contents of source_dir

REM local drive is where the files are copied tentatively
REM Note userprofile should be the home directory of the user automatically, i.e. C:\\Documents and Settings\myuseridnumber

IF NOT EXIST "%LOCAL_DEST_DIR%" ( 
GOTO MKLOCALDIR 
) ELSE ( GOTO SETLOCKS )

:MKLOCALDIR

ECHO Making local directory %LOCAL_DEST_DIR%
mkdir "%LOCAL_DEST_DIR%"

:SETLOCKS

cd %LOCAL_DEST_DIR%
REM Set the lock-files
SET SOURCE_COPIED_LOCK=source-lock.file
SET DEST_COPIED_LOCK=dest-lock.file

echo %SOURCE_COPIED_LOCK% > %EXCLUDES_FILE%
echo %DEST_COPIED_LOCK% >> %EXCLUDES_FILE%
echo %EXCLUDES_FILE% >> %EXCLUDES_FILE%

:CHECK_DESTCOPIED
REM Check if the destination has been reached, by checking the date of the destination-locked file
REM If it hasnt, then then check if the source has been copied
REM If it has, end the routine


ECHO Checking whether todays files have been copied already
IF EXIST %DEST_COPIED_LOCK% (
   ECHO Found the lock file %DEST_COPIED_LOCK%
   GOTO CHECKDESTLOCK
) ELSE (
  Echo  No destination lock file found
  GOTO CHECK_SRCCOPIED
)

:CHECKDESTLOCK
ECHO Checking whether the destination files were transferred today
FOR %%a in ( %DEST_COPIED_LOCK% ) DO SET DESTLOCKDATETIME=%%~ta
SET DestFileDate=%DESTLOCKDATETIME:~0,10%
IF %DestFileDate%==%DATE% ( 
   ECHO The files have already been copied today   
   GOTO ENDER 
) ELSE ( 
  ECHO The files have not been copied today
  GOTO CHECK_SRCCOPIED 
)

:CHECK_SRCCOPIED
REM Check for lock file, if it exists and is for the current date, then do not try to copy from the source file
REM The lockfile indicates that the source has been copied
ECHO Checking whether the source files have been copied already
IF EXIST %SOURCE_COPIED_LOCK% (
   ECHO Date-indicator found, checking it
   GOTO CHECK_SRCLOCK
) ELSE (
  ECHO They were not previously copied  
  GOTO MAPSRC
)   

:CHECK_SRCLOCK
ECHO Checking the date
FOR %%a in (%SOURCE_COPIED_LOCK%) DO SET LOCKFILEDATE=%%~ta
SET FileDate=%LOCKFILEDATE:~0,10%
IF %FileDate%==%DATE% ( 
   ECHO The files have been copied to the local machine today already
   GOTO MAPDEST 
) ELSE ( 
  Echo The files have NOT been copied to the local machine today
  GOTO MAPSRC 
)


:MAPSRC
ECHO Mapping network drive %SOURCE_DRIVE% to %SOURCE_SHARED_FOLDER%
REM net.exe use command maps the network drive
REM If you want to use a different user, add the following option:
REM USER:<DOMAIN>\<USERNAME>
net USE %SOURCE_DRIVE% %SOURCE_SHARED_FOLDER% /USER:%SOURCEDOMAIN%\%SOURCEUSER%

IF EXIST %SOURCE_DRIVE%\NUL (   
   GOTO COPYFROMSRC
) ELSE (
   GOTO ENDER
)

REM Copy folder from the source drive to the local drive
:COPYFROMSRC
IF EXIST %SOURCE_DIR%\NUL ( 
  ECHO Found folder %SOURCE_DIR%, copying contents  
  REM Now check for destination directory  
  GOTO COPYTOLOCAL
) ELSE (
   ECHO Source directory %SOURCE_DIR% not found. Please check that the directory exists.
   GOTO ENDER
)


:COPYTOLOCAL
REM Copy contents from source to local machine
SET BEFORE_DIR=%cd%
cd %LOCAL_DEST_DIR%
xcopy /S /Y "%SOURCE_DIR%\*" .
ECHO Removing the network-mapped drive %SOURCE_DRIVE%
net use %SOURCE_DRIVE% /delete
attrib -h %SOURCE_COPIED_LOCK%
echo null > %SOURCE_COPIED_LOCK%
attrib +h %SOURCE_COPIED_LOCK%
cd %BEFORE_DIR%
GOTO ENDER

:MAPDEST
ECHO Attemping to map %DEST_SHARED_DIR% to %DEST_DRIVE% for user %DESTDOMAIN%\%DESTUSER%
net USE %DEST_DRIVE% %DEST_SHARED_DIR% /USER:%DESTDOMAIN%\%DESTUSER%
REM it was successful, go to the copy
REM if it was not successful, exit
IF EXIST %DEST_DRIVE%\NUL (   
   GOTO COPYTODEST
) ELSE (
   GOTO ENDER
)

:COPYTODEST
REM If the destination directory exists, try copying to it. Otherwise, dont 
IF EXIST %DEST_DIR%\NUL ( 
  ECHO Found folder %DEST_DIR%, copying contents  
  REM Now check for destination directory  
  GOTO COPYFROMLOCAL
) ELSE (
   ECHO Destination directory %DEST_DIR% not found. Please check that the directory exists.
)


:COPYFROMLOCAL

SET BEFORE_DIR=%cd%
cd %LOCAL_DEST_DIR%
xcopy /S /Y /EXCLUDE:%EXCLUDES_FILE% .\* "%DEST_DIR%"
      
ECHO Removing the network-mapped drive %DEST_DRIVE%
net use %DEST_DRIVE% /delete
attrib -h %DEST_COPIED_LOCK%
echo null > %DEST_COPIED_LOCK%
attrib +h %DEST_COPIED_LOCK%
if not exist "%LOCAL_DEST_DIR%" GOTO ENDER
cd %LOCAL_DEST_DIR%
del /a:-h /q .\*
cd %BEFORE_DIR%
GOTO ENDER

:ENDER
REM return to original dir
cd %ORIG_DIR%
goto:eof

:USAGE
ECHO USAGE: s2s --source-drive-letter-- --source-drive-target-- --source-dir-- --dest-drive-letter-- --dest-drive-folder-- --dest-dir-in-dest-drive--
ECHO.
ECHO Example: s2s T \\source\drive\target source\dir\rel\to\drive U \\dest\drive\folder dest\dir\rel\to\drive
ECHO.
ECHO The purpose of this program is to copy files from source-drive to dest-drive, when they are not connected to the same network
ECHO.
ECHO This program, by being run twice, connected to source-drive-target and dest-drive-target on the first and second run, attempts to: 
ECHO.
ECHO ******FIRST RUN******
ECHO (a) attempt to map source-drive-target to source-drive-letter
ECHO (b) copy all files from source-dir, stored in source-drive-target, to local destination dir (%LOCAL_DEST_DIR%)
ECHO **********************
ECHO NOTE: The first run will be attempted on every run of the program until the files are copied successfully
ECHO.
ECHO Until the files are copied successfully, the first run will be run exclusively every time
ECHO.
ECHO ******SECOND RUN*****
ECHO Then, on the subsequent run, after files have been copied to the local folder, it will:
ECHO (c) attempt to map dest-drive-folder onto dest-drive-letter, 
ECHO (d) copy all files from local destination dir (%LOCAL_DEST_DIR%) to dest-dir-in-dest-drive
ECHO (e) delete all content files from %LOCAL_DEST_DIR%
ECHO *********************
ECHO.
ECHO Every day, the first run of the program will be run again. This program is not made to copy files multiple times within a single day. 
ECHO If someone wishes to add this functionality, they could remove the current 'lock-file' usage, which are used as indicators of when the last transfers took place
ECHO.
ECHO Warning: Be very cautious if you change the LOCAL_DEST_DIR variable, as it will NOT prompt you for deletion of all the files!! Therefore, it is set at the USERPROFILE\temp\transfer directory by default
ECHO If you have a solution for this issue, please email colin hilchey@mail.nissan.co.jp
