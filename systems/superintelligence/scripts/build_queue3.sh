#!/usr/bin/env bash
# Queue-3: mechanical activation. Gated on queue-2 completion (.queue2_done).
# Runs the threshold-gated activator: per built team, if VALIDATION PASS-rate clears
# THRESHOLD, flip registry built=true + regen /SI-<Short>-* commands. Top-up / SKILL
# prose / commit remain manual.
#
# Run detached:  nohup bash superintelligence/scripts/build_queue3.sh >/dev/null 2>&1 &
set -u
ROOT=/Users/Rijul_Kalra/projects/coco-platform/superintelligence
cd "$ROOT" || exit 1
LOG="$ROOT/scripts/queue3.log"
: > "$LOG"
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

say "QUEUE-3 START (pid $$). Gate: wait for queue-2 (.queue2_done)."
g=0
while [ ! -f "$ROOT/scripts/.queue2_done" ]; do
  sleep 60; g=$((g+1))
  if [ "$g" -gt 1200 ]; then say "GATE-GUARD tripped (~20h) — aborting"; exit 1; fi
done
say "queue-2 done. Running threshold-gated activation (THRESHOLD=${THRESHOLD:-0.70})."
python3 "$ROOT/scripts/activate_teams.py" >>"$LOG" 2>&1
say "activation complete. See ACTIVATION-REPORT.md."
say "MANUAL REMAINING: persona top-up (verify-gate), SKILL.md prose per team, git commit + push, re-run activate_teams.py for any HELD team after top-up."
touch "$ROOT/scripts/.queue3_done"
