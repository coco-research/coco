# Local-build quality findings — 2026-06-01 (during unattended run)

Two bugs found + fixed mid-run while the user was away. Builds kept running ($0); no data lost.

## Bug 1 — validator cutoff inverted (FIXED)

`validate_all.py` used `CUTOFF = "2026-06-01"` (today) but `recent_signal_12mo` means
"within the last 12 months" → cutoff must be **12 months ago = 2025-06-01** (what
`build_local` uses). With today's date, the validator demanded signals dated *after today*
→ impossible → **0/47 false-fail**. Fixed in all 7 `validate_all.py` copies. Finance
re-validated: 0→6 PASS.

## Bug 2 — output truncation at max_tokens=8000 (FIXED)

Biggest structural-failure class. The model writes a long frontmatter (signals + stances +
sources) then narrative; at `max_tokens=8000` it was **cut off mid-frontmatter** (frontmatter
never closes → "not a mapping" / unparseable). The content was *good* (real cited URLs,
proper block-YAML) — just incomplete. Raised `llm()` default **8000 → 11000** (safe under the
16384-tokens/slot at context=32768, parallel=2) in all 6 `build_local.py` copies. Trading's
next cell + GRC + queue-2 teams build with the higher cap.

## Finance yield (at max_tokens=8000, pre-fix) — the baseline to beat

| class | count | % | remedy |
|---|---|---|---|
| clean PASS | 6 | 13% | — |
| quota-short (real, thin sources/signals) | 14 | 30% | Claude top-up (verify-gate) |
| structural broken | 27 | 57% | rebuild |
| ├ truncated (good content, cut off) | 18 | | **Bug 2 fix should recover most** |
| ├ empty (1 byte) | 7 | | rebuild --force (maybe retry-on-empty) |
| └ wrong-schema | 2 | | rebuild --force |

**Expectation:** Trading (first team built with the 11000 fix) should show far fewer
truncation failures. That comparison validates the fix.

## Remaining decision for the user

1. **Re-run Finance structural fails** with the fix: `build_local.py --only <slug> --force`
   for the 27 (do AFTER the queue finishes — running it now contends for the 2 model slots
   and would slow Trading/GRC).
2. **Quota-short (14 + however many across teams)** → genuine Claude top-up; can't be local
   (verify-gate: real people, real cited sources).
3. If post-fix yield is still low, consider: retry-on-empty/unparseable loop in build_local,
   or fall back to Claude agents for the structural remainder.

## Structural-fail slugs (Finance, for --force rebuild)

empty: adam-tooze annie-duke david-birch frank-rotman howard-schilit marc-rubinstein morgan-housel
malformed(truncated): bill-ackman cathie-wood charlie-munger claudia-sahm dan-rasmussen jason-furman jay-ritter larry-summers matt-harris meir-statman mohamed-el-erian mohnish-pabrai nouriel-roubini richard-thaler seth-klarman simon-taylor tim-koller warren-buffett
wrong-schema: howard-marks jack-mccullough
