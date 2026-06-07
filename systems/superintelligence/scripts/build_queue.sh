#!/usr/bin/env bash
# Sequential team-build queue (local-first). Chains AFTER the in-flight Finance build:
#   wait Finance idle -> finalize Finance -> build Trading -> build GRC.
# Each team: 2 cell-partitioned workers (matches LM Studio PARALLEL=2 / 32k = 16k/slot),
# then build_registry -> build_cells -> validate_all (writes <team>/VALIDATION.md).
#
# Parked for human review (NOT done here, by design — verify-gate / judgment):
#   - SKILL.md prose per team
#   - superintelligence/registry.json meta flip built=true
#   - /SI-<team>-* command generation (build_commands.py TEAMS dict)
#   - Claude top-up of NEEDS-TOPUP personas
#
# Run detached:  nohup bash superintelligence/scripts/build_queue.sh >/dev/null 2>&1 &
set -u
ROOT=/Users/Rijul_Kalra/projects/coco-platform/superintelligence
cd "$ROOT" || exit 1
LOG="$ROOT/scripts/queue.log"
: > "$LOG"

say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

# wait until NO build_local.py process remains; require 2 consecutive empty polls
# (guards the sub-second gap between a worker's cells). Max ~6h guard.
wait_idle(){
  local tag="$1" empties=0 guard=0
  while :; do
    if pgrep -f build_local.py >/dev/null 2>&1; then
      empties=0
    else
      empties=$((empties+1))
      [ "$empties" -ge 2 ] && break
    fi
    sleep 30
    guard=$((guard+1))
    if [ "$guard" -gt 720 ]; then say "WAIT-GUARD tripped ($tag) after ~6h — proceeding"; break; fi
  done
}

finalize(){   # $1 = team dir name
  local t="$1"
  say "  finalize $t: registry -> cells -> validate"
  python3 "$ROOT/$t/scripts/build_registry.py" >>"$LOG" 2>&1 || say "  WARN registry $t failed"
  python3 "$ROOT/$t/scripts/build_cells.py"    >>"$LOG" 2>&1 || say "  WARN cells $t failed"
  python3 "$ROOT/$t/scripts/validate_all.py"   >>"$LOG" 2>&1 || say "  WARN validate $t failed"
  local built; built=$(ls "$ROOT/$t/personas/"*.md 2>/dev/null | wc -l | tr -d ' ')
  say "  $t finalized: $built persona files; see $t/VALIDATION.md"
}

build_team(){  # $1=team  $2=cellsA  $3=cellsB
  local t="$1" A="$2" B="$3"
  say "=== TEAM $t: launch 2 workers ==="
  ( cd "$ROOT/$t/scripts" || exit 1; for c in $A; do python3 build_local.py --cell "$c"; done ) \
      >"$ROOT/$t/scripts/workerA.log" 2>&1 &
  ( cd "$ROOT/$t/scripts" || exit 1; for c in $B; do python3 build_local.py --cell "$c"; done ) \
      >"$ROOT/$t/scripts/workerB.log" 2>&1 &
  sleep 6
  wait_idle "$t"
  say "=== TEAM $t: build idle ==="
  finalize "$t"
}

say "QUEUE START (pid $$). Stage 0: wait for in-flight Finance workers."
wait_idle finance
say "Stage 1: Finance idle -> finalize."
finalize finance

say "Stage 2: Trading (46 personas / 8 cells)."
build_team trading \
  "macro-discretionary quant-systematic derivatives-volatility microstructure-execution" \
  "fixed-income-rates risk-systemic crypto-digital-assets trader-craft-psychology"

say "Stage 3: Risk & Compliance / GRC (30 native / 5 native cells; cross-list cells skip)."
build_team risk-compliance \
  "privacy-data-protection ai-governance-responsible-ai" \
  "regulatory-tech-policy erm-grc-leadership financial-crime-aml"

say "QUEUE COMPLETE."
say "MANUAL REVIEW REMAINING: SKILL.md prose (trading, risk-compliance); flip superintelligence/registry.json built=true; regen /SI-Trade-* + /SI-GRC-* via build_commands.py; Claude top-up of NEEDS-TOPUP (see each VALIDATION.md)."
touch "$ROOT/scripts/.queue_done"
