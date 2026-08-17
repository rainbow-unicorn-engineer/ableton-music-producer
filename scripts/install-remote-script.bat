@echo off
REM ============================================================
REM  XLNT Studio - install the merged Remote Script into Ableton
REM
REM  Copies the repo's AbletonMCP (now TCP + UDP in one script)
REM  over the copy Ableton actually loads.
REM
REM  CLOSE ABLETON FIRST. Then run this by double-clicking, or:
REM      scripts\install-remote-script.bat
REM  If the copy fails with "Access denied", right-click ->
REM  Run as administrator.
REM ============================================================

set "SRC=%~dp0..\ableton-mcp\remote_script\AbletonMCP"
set "DST=C:\ProgramData\Ableton\Live 12 Suite\Resources\MIDI Remote Scripts\AbletonMCP"

if not exist "%SRC%\__init__.py" (
    echo Could not find the source script at %SRC%
    exit /b 1
)
if not exist "C:\ProgramData\Ableton\Live 12 Suite" (
    echo Ableton Live 12 Suite not found in the usual place - edit DST
    echo in this script to match your install, then re-run.
    exit /b 1
)

echo Installing merged AbletonMCP (TCP 9877 + UDP 9878)...
xcopy /Y /I "%SRC%\*.py" "%DST%\" >nul
if errorlevel 1 (
    echo Copy failed - close Ableton and/or run as administrator.
    exit /b 1
)

REM Clear stale compiled copies so Live loads the new code
if exist "%DST%\__pycache__" rmdir /S /Q "%DST%\__pycache__"

echo.
echo Done. Now:
echo   1. Open Ableton
echo   2. Preferences ^> Link, Tempo ^& MIDI ^> Control Surface: AbletonMCP
echo      (the AbletonMCP_UDP entry is retired - don't select it)
echo   3. You should see "AbletonMCP: Listening..." and the log line
echo      "UDP performance plane started on port 9878"
exit /b 0
