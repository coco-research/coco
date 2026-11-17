#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -B tests/test_agents_descriptions.py
