#!/usr/bin/env bash
# create_nuitka_exe.sh — Build the onefile Linux executable with Nuitka
# Uses the .venv-build environment (created by setup.sh), so nothing is
# installed into your global Python. The C compiler (gcc) remains a system
# component; patchelf is required by Nuitka --onefile on Linux.
# Usage:  ./create_nuitka_exe.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PY="$SCRIPT_DIR/.venv-build/bin/python"

if [[ ! -x "$PY" ]]; then
    echo "No build environment found." >&2
    echo "Create it first:" >&2
    echo "    ./setup.sh" >&2
    exit 1
fi

for tool in gcc patchelf; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "error: '$tool' not found — required for the Nuitka build." >&2
        echo "       On Debian/Ubuntu: sudo apt install gcc patchelf" >&2
        exit 1
    fi
done

"$PY" -m nuitka \
    --include-data-file=res/default.css=res/default.css \
    --include-data-file=res/functions.js=res/functions.js \
    --include-data-file=res/logo_base64.txt=res/logo_base64.txt \
    --include-data-file=res/logo.png=res/logo.png \
    --onefile \
    --assume-yes-for-downloads \
    il_conv.py

echo ""
echo "Build finished: $SCRIPT_DIR/il_conv.bin"