@echo off
rem setup.cmd -- Create the il_conv Python virtual environments (Windows native)
rem Creates:
rem   .venv       dev environment: runtime deps + coverage -- used by run_tests.cmd
rem   .venv-build  build environment: runtime deps + nuitka -- used by create_nuitka_exe.bat
rem Usage:  setup.cmd              default interpreter (python on PATH)
rem         set PYTHON=python3.12  force a specific base interpreter

setlocal
set PROJ_DIR=%~dp0
set PROJ_DIR=%PROJ_DIR:~0,-1%

set PYTHON_BIN=python
if defined PYTHON set PYTHON_BIN=%PYTHON%

%PYTHON_BIN% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo error: %PYTHON_BIN% is too old - il_conv requires Python ^>= 3.10
    exit /b 1
)

%PYTHON_BIN% -m venv --help >nul 2>&1
if errorlevel 1 (
    echo error: %PYTHON_BIN% cannot create venvs ^(missing 'venv' module^)
    exit /b 1
)

echo Base interpreter: %PYTHON_BIN%
%PYTHON_BIN% --version

if exist "%PROJ_DIR%\.venv\Scripts\python.exe" (
    echo ==^> .venv already exists - keeping it
) else (
    echo ==^> Creating .venv
    %PYTHON_BIN% -m venv "%PROJ_DIR%\.venv"
)

if exist "%PROJ_DIR%\.venv-build\Scripts\python.exe" (
    echo ==^> .venv-build already exists - keeping it
) else (
    echo ==^> Creating .venv-build
    %PYTHON_BIN% -m venv "%PROJ_DIR%\.venv-build"
)

echo ==^> Installing dependencies into .venv
"%PROJ_DIR%\.venv\Scripts\python.exe" -m pip install --upgrade pip
"%PROJ_DIR%\.venv\Scripts\python.exe" -m pip install -r "%PROJ_DIR%\requirements.txt"
if errorlevel 1 (
    echo.
    echo FAILED installing .venv dependencies.
    exit /b 1
)

echo ==^> Installing dependencies into .venv-build
"%PROJ_DIR%\.venv-build\Scripts\python.exe" -m pip install --upgrade pip
"%PROJ_DIR%\.venv-build\Scripts\python.exe" -m pip install -r "%PROJ_DIR%\requirements.txt" nuitka ordered-set zstandard
if errorlevel 1 (
    echo.
    echo FAILED installing .venv-build dependencies.
    exit /b 1
)

echo.
echo Done. Next steps:
echo   run_tests.cmd            run the test suite
echo   create_nuitka_exe.bat    local Nuitka onefile build