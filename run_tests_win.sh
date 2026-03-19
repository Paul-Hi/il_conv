#!/usr/bin/env bash
# run_tests_win.sh — Run run_tests.cmd via Windows cmd.exe from WSL
# Usage:  ./run_tests_win.sh          # run all tests (normal output)
#         ./run_tests_win.sh -v       # verbose output (one line per test)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMD_PATH="$(wslpath -w "$SCRIPT_DIR/run_tests.cmd")"

/mnt/c/WINDOWS/system32/cmd.exe /c "$CMD_PATH" ${1:+"$1"}
