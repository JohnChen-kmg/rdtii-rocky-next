@echo off
rem Builds the PDF of every .tex file in this folder. Double-click this file, or run it from a window.
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
    echo Without installing anything: upload the .tex file to https://www.overleaf.com
    echo as a new project, press Recompile and download the PDF from there.
    call :hold
    exit /b 1
)

for %%f in (*.tex) do (
    call :build "%%~nf"
    if errorlevel 1 goto failed
)
echo.
call :hold
exit /b 0

:build
rem Twice: the first pass records the cross-references, the second pass prints them.
pdflatex -interaction=nonstopmode -halt-on-error "%~1.tex" || exit /b 1
pdflatex -interaction=nonstopmode -halt-on-error "%~1.tex" || exit /b 1
echo Built %~1.pdf
exit /b 0

:failed
echo.
echo pdflatex stopped with an error. The details are in the .log file beside the .tex.
call :hold
exit /b 1

:hold
rem When the file was double-clicked, keep the window open so the message can be read.
echo %cmdcmdline% | "%SystemRoot%\System32\find.exe" /i "%SELF%" >nul && pause
exit /b 0
