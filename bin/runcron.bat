cd %HOME%

SET LOGDIR=logs\%DATE%
mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\cronjobs.log

"%HOME_BIN%\cronjobs.bat" > "%LOGFILE%"