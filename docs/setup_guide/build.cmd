@echo off
rem Builds SETUP_GUIDE.pdf from SETUP_GUIDE.tex. Double-click this file, or run it from a window.
setlocal
set "SELF=%~nx0"
cd /d "%~dp0"

where pdflatex >nul 2>nul
if errorlevel 1 (
    echo pdflatex was not found on this computer.
    echo.
    echo One-time install, then close this window, open a new one and run build.cmd again:
    echo     winget install MiKTeX.MiKTeX
    echo.
    echo Without installing anything: upload SETUP_GUIDE.tex to https://www.overleaf.com
    echo as a new project, press Recompile and download the PDF from there.
    call :hold
    exit /b 1
)

rem Twice: the first pass records the cross-references, the second pass prints them.
pdflatex -interaction=nonstopmode -halt-on-error SETUP_GUIDE.tex
if errorlevel 1 goto failed
pdflatex -interaction=nonstopmode -halt-on-error SETUP_GUIDE.tex
if errorlevel 1 goto failed

echo.
echo Built SETUP_GUIDE.pdf
call :hold
exit /b 0

:failed
echo.
echo pdflatex stopped with an error. The details are in SETUP_GUIDE.log.
call :hold
exit /b 1

:hold
rem When the file was double-clicked, keep the window open so the message can be read.
echo %cmdcmdline% | "%SystemRoot%\System32\find.exe" /i "%SELF%" >nul && pause
exit /b 0
