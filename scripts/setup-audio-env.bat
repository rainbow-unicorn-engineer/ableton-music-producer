@echo off
REM ============================================================
REM  XLNT Studio - one-time audio-model environment setup
REM
REM  Creates a Python 3.11 conda env ("xlnt-audio"), installs
REM  Demucs (stem separation) + basic-pitch (polyphonic MIDI),
REM  and points the XLNT_DEMUCS environment variable at it so
REM  the ears tools find it automatically.
REM
REM  HOW TO RUN: open "Anaconda Prompt" from the Start menu, then:
REM      cd C:\Users\gavin\PycharmProjects\xlnt-studio
REM      scripts\setup-audio-env.bat
REM
REM  Afterwards: restart Claude Desktop. Done.
REM ============================================================

echo [1/4] Creating Python 3.11 environment "xlnt-audio"...
call conda create -n xlnt-audio python=3.11 -y
if errorlevel 1 goto :err

echo [2/4] Installing Demucs (this pulls PyTorch - a few GB, be patient)...
call conda run -n xlnt-audio pip install demucs
if errorlevel 1 goto :err

echo [3/5] Installing basic-pitch (polyphonic audio-to-MIDI)...
call conda run -n xlnt-audio pip install basic-pitch
if errorlevel 1 echo   basic-pitch failed - not fatal, MIDI extraction falls back to monophonic mode. Continuing.

echo [4/5] Installing laion-clap (vibe search - "meaning space" for sounds)...
REM torchvision: laion-clap imports it but forgets to declare it (known wart)
call conda run -n xlnt-audio pip install laion-clap torchvision
if errorlevel 1 echo   laion-clap failed - not fatal, vibe search stays off until installed. Continuing.

echo [5/5] Pointing XLNT_DEMUCS / XLNT_AUDIO_PY at the new environment...
for /f "delims=" %%i in ('conda run -n xlnt-audio python -c "import sys; print(sys.executable)"') do set "XLNT_PY=%%i"
if not defined XLNT_PY goto :err
setx XLNT_DEMUCS "%XLNT_PY%"
setx XLNT_AUDIO_PY "%XLNT_PY%"

echo.
echo ============================================================
echo  Done. XLNT_DEMUCS = XLNT_AUDIO_PY = %XLNT_PY%
echo  Now RESTART CLAUDE DESKTOP so the tools pick it up.
echo  (First stem separation downloads the ~1 GB Demucs model;
echo   first CLAP use downloads a ~2 GB checkpoint.)
echo.
echo  To switch on vibe search, run the overnight embedding scan:
echo    conda run -n xlnt-audio python library-analyst\embeddings.py --scan
echo ============================================================
exit /b 0

:err
echo.
echo Something failed - copy everything above into the Claude chat
echo and I'll sort it out.
exit /b 1
