#!/usr/bin/env bash
# Nano build queue — rebuilds ALL teams via gpt-5.4-nano (replaces the local qwen queues).
# Per team: build_nano.py --all --force (5-parallel API) -> build_registry -> build_cells ->
# validate_all. API-bound, not GPU-bound. ~$0.50 total, ~30-45 min.
#
# Run detached:  nohup bash superintelligence/scripts/build_queue_nano.sh >/dev/null 2>&1 &
set -u
ROOT=/Users/user/projects/coco-platform/superintelligence
cd "$ROOT" || exit 1
LOG="$ROOT/scripts/queue_nano.log"
: > "$LOG"
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

TEAMS="finance trading risk-compliance strategy data-analytics gtm"

finalize(){
  local t="$1"
  say "  finalize $t: registry -> cells -> validate"
  python3 "$ROOT/$t/scripts/build_registry.py" >>"$LOG" 2>&1 || say "  WARN registry $t"
  python3 "$ROOT/$t/scripts/build_cells.py"    >>"$LOG" 2>&1 || say "  WARN cells $t"
  python3 "$ROOT/$t/scripts/validate_all.py"   >>"$LOG" 2>&1 || say "  WARN validate $t"
  local pass; pass=$(grep -oE '[0-9]+/[0-9]+ PASS' "$ROOT/$t/VALIDATION.md" 2>/dev/null | head -1)
  say "  $t done — VALIDATION: ${pass:-?}"
}

say "NANO QUEUE START (pid $$). Model gpt-5.4-nano via QB gateway."
for t in $TEAMS; do
  say "=== TEAM $t: nano build (--all --force) ==="
  python3 "$ROOT/$t/scripts/build_nano.py" --all --force >>"$LOG" 2>&1 || say "  WARN build $t returned nonzero"
  finalize "$t"
done
say "NANO QUEUE COMPLETE."
say "Next: queue-3 activation (registry built=true + /SI-* regen, threshold-gated) — run activate_teams.py."
touch "$ROOT/scripts/.nano_done"
