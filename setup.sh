#!/usr/bin/env bash
# setup.sh — Create the il_conv Python virtual environments (Linux/WSL)
# Creates:
#   .venv        dev environment (runtime deps + coverage) — used by run_tests.sh
#   .venv-build  build environment (runtime deps + nuitka)  — used by create_nuitka_exe.sh
# Usage:  ./setup.sh                  # default interpreter selection
#         PYTHON=python3.12 ./setup.sh   # force a specific base interpreter

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

pick_interpreter() {
    if [[ -n "${PYTHON:-}" ]]; then
        PYTHON_BIN="$PYTHON"
        return
    fi
    for candidate in python3.12 python3.11 python3.10 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            PYTHON_BIN="$candidate"
            return
        fi
    done
    echo "error: no python3 found on PATH" >&2
    exit 1
}

check_version_and_venv() {
    if ! "$PYTHON_BIN" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
        echo "error: $PYTHON_BIN is too old — il_conv requires Python >= 3.10" >&2
        exit 1
    fi
    if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
        echo "error: $PYTHON_BIN cannot create venvs (missing 'venv' module)." >&2
        echo "       On Debian/Ubuntu install e.g.: sudo apt install python3.12-venv" >&2
        exit 1
    fi
}

create_venv() {
    local name="$1"
    if [[ -x "$name/bin/python" ]]; then
        echo "==> $name already exists — keeping it"
    else
        echo "==> Creating $name (base: $PYTHON_BIN)"
        "$PYTHON_BIN" -m venv "$name"
    fi
}

install_deps() {
    local name="$1"
    shift
    echo "==> Installing dependencies into $name"
    "$name/bin/python" -m pip install --upgrade pip
    "$name/bin/python" -m pip install "$@"
}

pick_interpreter
check_version_and_venv
echo "Base interpreter: $PYTHON_BIN ($("$PYTHON_BIN" --version 2>&1))"

create_venv ".venv"
install_deps ".venv" -r requirements.txt

create_venv ".venv-build"
install_deps ".venv-build" -r requirements.txt nuitka ordered-set zstandard

echo ""
echo "Done. Next steps:"
echo "  ./run_tests.sh                          # run the test suite"
echo "  ./create_nuitka_exe.sh                  # local Nuitka onefile build"