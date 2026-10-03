@echo off
rem RDTII Rocky: double-click to open the interface in a window of its own.
rem Closing the window stops it. Nothing is installed; Python 3.10 or newer is all it needs.
setlocal
cd /d "%~dp0"

rem A Python without a console window, so only the tool's window shows.
set "PY="
if exist ".venv\Scripts\pythonw.exe" set "PY=.venv\Scripts\pythonw.exe"
if not defined PY for %%P in (pyw.exe pythonw.exe) do if not defined PY where %%P >nul 2>nul && set "PY=%%P"
if defined PY (
  start "" "%PY%" "interface\app.py" --window %*
  exit /b 0
)

rem No windowless Python: run with a console, which stays open while the tool runs.
for %%P in (py.exe python.exe) do if not defined PY where %%P >nul 2>nul && set "PY=%%P"
if defined PY (
  "%PY%" "interface\app.py" --window %*
  exit /b %errorlevel%
)

echo Python 3.10 or newer is needed and was not found.
echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH",
echo then double-click this file again.
pause
exit /b 1
