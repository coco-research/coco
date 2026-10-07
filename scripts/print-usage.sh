#!/usr/bin/env bash
# Extracts and prints the header comments of a script as usage.
# Usage: bash scripts/print-usage.sh "$0"

if [[ $# -ne 1 ]]; then
  echo "Usage: bash scripts/print-usage.sh <script-file>" >&2
  exit 1
fi

# Blank lines inside the header are kept only when another comment line follows them.
awk 'NR == 1 { next } /^[[:space:]]*$/ { blank++; next }
     /^#/ { while (blank > 0) { print ""; blank-- } sub(/^# ?/, ""); print; next } { exit }' "$1"
