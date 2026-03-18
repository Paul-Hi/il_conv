#!/usr/bin/env bash
# run_tests.sh — Run all unit tests for il_conv with code coverage
# Usage:  ./run_tests.sh          # run all test_*.py files
#         ./run_tests.sh -v       # verbose output
# Coverage config is in .coveragerc

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERBOSITY="${1:-}"

echo "========================================="
echo "  il_conv unit tests"
echo "========================================="

python3 -m coverage run -m unittest discover \
    --start-directory tests \
    --pattern "test_*.py" \
    --top-level-directory . \
    $VERBOSITY

echo ""
echo "========================================="
echo "  Coverage report"
echo "========================================="
python3 -m coverage report

echo ""
echo "All tests passed."
