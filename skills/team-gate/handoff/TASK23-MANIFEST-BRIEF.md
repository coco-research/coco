# Task 23, step 3: the brownfield map joins the ship manifest

This is a scoped change to committed, verified task 7 files: skills/team-gate/references/ship-manifest.json, skills/team-gate/scripts/fixtures/check_artifacts/make_fixtures.py, and the check_artifacts self-test case list. It lands only after brownfield_map.py has passed its round-2 verification and been committed, because the manifest entry names an artifact that script writes. The opening line of the builder message is "You never run git commit, git add, or git push; the brain commits."

## The change

ship-manifest.json, stage 1 (Research) `outputs` gains one entry for `.team-ship/BROWNFIELD-MAP.md` with `minLines` 12, `requiredHeadings` ["Summary", "Impact", "Tests", "Limits"], and the same `forbidTokens` list the other artifacts carry. Stage 2 (Think) `inputs` gains the identical entry, so Think cannot open without the map. No other stage, key or entry changes; the `approval` key and the fourteen stage numbers stay exactly as they are.

Why these values, and one measurement the builder makes first. check_artifacts.validate_artifact counts non-blank, non-heading lines against minLines and maxLines and tests each requiredHeadings entry with has_required_heading; there is no check on the body under a heading. brownfield_map.py renders five headings (Summary, Entry points, Impact, Tests, Limits) and a greenfield repository still renders all five with "none identified" bodies. Before editing the manifest, run brownfield_map.py against the greenfield fixture (fixtures/brownfield_map/_build/greenfield with the stub binary on RIPWIRE_BIN) and count its non-blank non-heading lines with check_artifacts.count_non_trivial_lines; minLines is the smaller of 12 and that count minus one, and the report states the measured count. No maxLines: a large repository's map is legitimately long. Entry points is left out of requiredHeadings because the other four carry the judgement the model needs at stage 2. Confirm with has_required_heading on a real map that each of the four required names matches its rendered heading line. The map is an addition to the stage 1 outputs; ship.md's stage list does not change, and the map is not a rename of any existing artifact.

## Fixtures

Every check_artifacts fixture that models a complete stage 1 output set or a complete stage 2 input set gains the map file, rendered by hand from the fixture's fixed content with the five headings and at least twelve lines, no wall-clock, no forbidden tokens. One new fixture, `map-missing`: stage-inputs 2 with the stage 2 brief present and `.team-ship/BROWNFIELD-MAP.md` absent; expected exit 1 and a stderr reason naming `BROWNFIELD-MAP.md`. The self-test grows by one line. Every existing case must keep its exit and its reason substring; a case that starts failing because the map is missing from its fixture is a defect in the fixture, not a finding.

## Verification, scoped Sonnet round

1. Full `check_artifacts.py --self-test` with TEAM_FIXED_TS pinned and TEAM_STATE_ROOT temporary; every case OK including map-missing.
2. `python3 -c` load of ship-manifest.json: fourteen stage keys plus approval; stage 1 outputs and stage 2 inputs each contain exactly one BROWNFIELD-MAP.md entry with the values above; every other entry byte-identical to the committed manifest (diff the committed file against the working file and confirm the diff touches only the two additions).
3. Live: generate a map with brownfield_map.py against a scratch repository with a run, then run `check_artifacts.py stage-output 1 .team-ship/BROWNFIELD-MAP.md --repo-root <repo>` and expect exit 0; delete the file and run `stage-inputs 2` and expect exit 1 naming the map.
4. ship_gate.py and fix_gate.py self-tests still pass, because ship_gate reads the manifest for stage names and artifact lists and its fixtures model complete stages; if a ship_gate fixture now lacks the map for stage 1 and starts failing, the fixture gains the map and the round records that.
5. Fresh fixture generation diffed against the in-tree _build, excluding .git, is empty.
6. Em dash and section sign grep across the changed files is empty.

## After both land

run_fixtures.sh gains `brownfield_map.py` and `hooks_selftest.py` in its script list, and the clean-checkout proof (git worktree add --detach into a temporary directory, run, remove) is rerun and quoted.
