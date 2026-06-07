#!/usr/bin/env bash
# Second build queue: Strategy -> Data & Analytics -> GTM.
# Gated: waits for queue-1 (.queue_done) AND for any build_local.py to be idle,
# so it only starts after Finance/Trading/GRC fully finish. Same 2-worker / cell-split
# pattern. Writes <team>/VALIDATION.md per team. Parks the same manual review items.
#
# Run detached:  nohup bash superintelligence/scripts/build_queue2.sh >/dev/null 2>&1 &
set -u
ROOT=/Users/Rijul_Kalra/projects/coco-platform/superintelligence
cd "$ROOT" || exit 1
LOG="$ROOT/scripts/queue2.log"
: > "$LOG"
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

wait_idle(){
  local tag="$1" empties=0 guard=0
  while :; do
    if pgrep -f build_local.py >/dev/null 2>&1; then empties=0
    else empties=$((empties+1)); [ "$empties" -ge 2 ] && break; fi
    sleep 30; guard=$((guard+1))
    if [ "$guard" -gt 720 ]; then say "WAIT-GUARD tripped ($tag) — proceeding"; break; fi
  done
}

finalize(){
  local t="$1"
  say "  finalize $t: registry -> cells -> validate"
  python3 "$ROOT/$t/scripts/build_registry.py" >>"$LOG" 2>&1 || say "  WARN registry $t failed"
  python3 "$ROOT/$t/scripts/build_cells.py"    >>"$LOG" 2>&1 || say "  WARN cells $t failed"
  python3 "$ROOT/$t/scripts/validate_all.py"   >>"$LOG" 2>&1 || say "  WARN validate $t failed"
  local built; built=$(ls "$ROOT/$t/personas/"*.md 2>/dev/null | wc -l | tr -d ' ')
  say "  $t finalized: $built persona files; see $t/VALIDATION.md"
}

build_team(){
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

say "QUEUE-2 START (pid $$). Gate: wait for queue-1 (.queue_done)."
g=0
while [ ! -f "$ROOT/scripts/.queue_done" ]; do
  sleep 60; g=$((g+1))
  if [ "$g" -gt 600 ]; then say "GATE-GUARD tripped (~10h) — proceeding anyway"; break; fi
done
say "queue-1 done. Ensuring build_local idle before starting."
wait_idle gate

say "Stage A: Strategy (31 / 7 cells)."
build_team strategy \
  "competitive-strategy-advantage growth-innovation corporate-portfolio-strategy" \
  "strategy-execution-org game-theory-decision behavioral-strategy-bias platform-ecosystem-strategy"

say "Stage B: Data & Analytics (29 / 7 cells)."
build_team data-analytics \
  "data-engineering-architecture analytics-engineering-modern-stack mlops-ml-systems" \
  "data-science-statistics data-visualization data-governance-quality experimentation-causal-inference"

say "Stage C: GTM (25 native / 7 cells)."
build_team gtm \
  "category-design-positioning demand-gen-content-marketing sales-methodology-negotiation" \
  "product-led-growth brand-strategy pricing-monetization customer-success-retention"

say "QUEUE-2 COMPLETE."
say "MANUAL REVIEW REMAINING (all 3): SKILL.md prose; flip superintelligence/registry.json built=true + counts; regen /SI-Strat-* + /SI-Data-* + /SI-GTM-* via build_commands.py TEAMS dict; Claude top-up of NEEDS-TOPUP (see each VALIDATION.md)."
touch "$ROOT/scripts/.queue2_done"
