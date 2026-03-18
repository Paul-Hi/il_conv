@echo off
setlocal

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" run_tests.py
) else (
    python run_tests.py
)
