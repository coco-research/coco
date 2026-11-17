#!/usr/bin/env bash
# Verify every pinned blob/reference and link only into a synthetic target.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -B tests/test_gsd_runtime.py
