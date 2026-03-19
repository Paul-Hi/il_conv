@echo off
rem run_tests.cmd -- Run all unit tests for il_conv with code coverage
rem Usage:  run_tests.cmd        run all tests (normal output)
rem         run_tests.cmd -v     verbose output (one line per test)
rem Coverage config is in .coveragerc

rem Capture project root before changing directory.
rem Strip trailing backslash from %~dp0 so quoted paths like "%PROJ_DIR%"
rem are safe (a trailing \ before " would escape the closing quote in cmd).
set PROJ_DIR=%~dp0
set PROJ_DIR=%PROJ_DIR:~0,-1%

rem Change to %TEMP% so SQLite files (.db, .coverage) are created on the
rem Windows filesystem instead of the WSL path, avoiding SQLite locking issues.
cd /d %TEMP%

echo =========================================
echo   il_conv unit tests
echo =========================================

python -m coverage erase

python -m coverage run -m unittest discover ^
    --start-directory "%PROJ_DIR%\tests" ^
    --pattern "test_*.py" ^
    --top-level-directory "%PROJ_DIR%" ^
    %1

if errorlevel 1 (
    echo.
    echo FAILED.
    exit /b 1
)

echo.
echo =========================================
echo   Coverage report
echo =========================================
python -m coverage report --rcfile="%PROJ_DIR%\.coveragerc"

echo.
echo All tests passed.
