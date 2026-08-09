#!/usr/bin/env bash
# run_tests.sh — Run all unit tests for il_conv with code coverage
# Usage:  ./run_tests.sh          # run all test_*.py files
#         ./run_tests.sh -v       # verbose output
#         PYTHON=python3.12 ./run_tests.sh   # force a specific interpreter
# Coverage config is in .coveragerc

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERBOSITY="${1:-}"

# Use the project venv by default (see setup.sh). PYTHON can override it.
PYTHON_BIN="${PYTHON:-"$SCRIPT_DIR/.venv/bin/python"}"

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "error: no virtual environment found." >&2
    echo "       Run: ./setup.sh" >&2
    exit 1
fi
if ! "$PYTHON_BIN" -c "import coverage, openpyxl, bs4, lxml, PIL" >/dev/null 2>&1; then
    echo "error: $PYTHON_BIN is missing the project requirements." >&2
    echo "       Re-run: ./setup.sh" >&2
    exit 1
fi

echo "Using interpreter: $PYTHON_BIN ($("$PYTHON_BIN" --version 2>&1))"
echo "========================================="
echo "  il_conv unit tests"
echo "========================================="

"$PYTHON_BIN" -m coverage run -m unittest discover \
    --start-directory tests \
    --pattern "test_*.py" \
    --top-level-directory . \
    $VERBOSITY

echo ""
echo "========================================="
echo "  Coverage report"
echo "========================================="
"$PYTHON_BIN" -m coverage report

echo ""
echo "All tests passed."
