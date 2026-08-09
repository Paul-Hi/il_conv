@echo off
rem create_nuitka_exe.bat -- Build the onefile Windows executable with Nuitka
rem Uses the .venv-build environment (created by setup.cmd), so nothing is
rem installed into your global Python. The C compiler (MinGW64 gcc) remains a
rem system component; Nuitka --mingw64 is used here.
rem Usage:  create_nuitka_exe.bat

rem Capture project root before changing directory.
set PROJ_DIR=%~dp0
set PROJ_DIR=%PROJ_DIR:~0,-1%

set PY=%PROJ_DIR%\.venv-build\Scripts\python.exe

if not exist "%PY%" (
    echo No build environment found.
    echo Create it first:
    echo     setup.cmd
    exit /b 1
)

cd /d "%PROJ_DIR%"

"%PY%" -m nuitka --include-data-file=res/default.css=res/default.css --include-data-file=res/functions.js=res/functions.js --include-data-file=res/logo_base64.txt=res/logo_base64.txt --include-data-file=res/logo.png=res/logo.png --onefile --mingw64 --assume-yes-for-downloads il_conv.py
