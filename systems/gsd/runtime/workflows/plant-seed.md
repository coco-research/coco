<purpose>
Capture a forward-looking idea as a structured seed file with trigger conditions.
Seeds auto-surface during /gsd:new-milestone when trigger conditions match the
new milestone's scope.

Seeds beat deferred items because they:
- Preserve WHY the idea matters (not just WHAT)
- Define WHEN to surface (trigger conditions, not manual scanning)
- Track breadcrumbs (code references, related decisions)
- Auto-present at the right time via new-milestone scan

**One-shot capture**: the seed file is written immediately from the idea text alone.
Trigger / Why / Scope are optional enrichment — they can be provided now or added
later. The file is never gated behind questions.
</purpose>

<process>

<step name="parse-idea">
Parse `$ARGUMENTS` for the idea summary.

First, check for an enrich flag:

```bash
if echo "$ARGUMENTS" | grep -qE '\-\-enrich[[:space:]]+SEED-[0-9]+'; then
  ENRICH_TARGET=$(echo "$ARGUMENTS" | grep -oE 'SEED-[0-9]+')
  SEED_FILE=$(ls .planning/seeds/${ENRICH_TARGET}-*.md 2>/dev/null | head -1)
  # Skip to enrich-seed step — do not prompt for $IDEA
else
  if [ -n "$ARGUMENTS" ]; then
    IDEA="$ARGUMENTS"
  else
    # Ask only when no arguments at all
    # What's the idea? (one sentence)
    IDEA="<user response>"
  fi
fi
```

If `$ENRICH_TARGET` is set, skip straight to the `enrich-seed` step. Do not set `$IDEA` and do not run `create-seed-dir`, `generate-seed-id`, `write-seed`, `collect-breadcrumbs`, `commit-seed`, or `confirm`.

If `$ARGUMENTS` is non-empty and contains no `--enrich` flag, treat the full value as `$IDEA` (no prompt).

Only prompt for the idea when `$ARGUMENTS` is empty and no enrich target is present. Store the response as `$IDEA`.
