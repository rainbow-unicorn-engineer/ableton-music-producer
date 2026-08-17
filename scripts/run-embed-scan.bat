@echo off
REM ============================================================
REM  XLNT Studio - run the CLAP embedding scan (vibe search fuel)
REM
REM  Run this from ANYWHERE (it finds the repo itself):
REM      scripts\run-embed-scan.bat
REM  or just double-click it.
REM
REM  First run downloads the ~2 GB CLAP checkpoint, then embeds
REM  every analyzed sample (~45k files - let it run overnight).
REM  Safe to close and re-run any time: it resumes where it left
REM  off. Progress prints as it goes.
REM ============================================================

call conda run --no-capture-output -n xlnt-audio python "%~dp0..\library-analyst\embeddings.py" --scan
if errorlevel 1 (
    echo.
    echo Scan hit an error - copy the output above into the Claude chat.
    exit /b 1
)
echo.
echo Embedding scan complete. Vibe search is live - try:
echo   "find me sounds like 'haunted carousel music box'"
exit /b 0
