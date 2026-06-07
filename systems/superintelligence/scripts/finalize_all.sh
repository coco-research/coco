#!/usr/bin/env bash
# Post-Claude-build finalize chain: YAML-repair -> per-team registry/cells/validate -> activate.
#   nohup bash superintelligence/scripts/finalize_all.sh >/dev/null 2>&1 &
set -u
ROOT=/Users/user/projects/coco-platform/superintelligence
cd "$ROOT" || exit 1
LOG="$ROOT/scripts/finalize.log"; : > "$LOG"
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
TEAMS="finance trading risk-compliance strategy data-analytics gtm"

say "STEP 1: nano YAML-repair across all teams"
python3 "$ROOT/scripts/yaml_repair.py" >>"$LOG" 2>&1 || say "WARN yaml_repair nonzero"

for t in $TEAMS; do
  say "STEP 2 ($t): registry -> cells -> validate"
  python3 "$ROOT/$t/scripts/build_registry.py" >>"$LOG" 2>&1 || say "  WARN registry $t"
  python3 "$ROOT/$t/scripts/build_cells.py"    >>"$LOG" 2>&1 || say "  WARN cells $t"
  python3 "$ROOT/$t/scripts/validate_all.py"   >>"$LOG" 2>&1 || say "  WARN validate $t"
  say "  $t: $(grep -oE '[0-9]+/[0-9]+ PASS' "$ROOT/$t/VALIDATION.md" 2>/dev/null|head -1)"
done

say "STEP 3: activate (flip built=true + regen /SI-* for teams >=70% PASS)"
python3 "$ROOT/scripts/activate_teams.py" >>"$LOG" 2>&1 || say "WARN activate"
say "FINALIZE COMPLETE. See ACTIVATION-REPORT.md + per-team VALIDATION.md"
touch "$ROOT/scripts/.finalize_done"
