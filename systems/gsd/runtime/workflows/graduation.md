# graduation.md — LEARNINGS.md Cross-Phase Graduation Helper

**Invoked by:** `transition.md` step `graduation_scan`. Never invoked directly by users.

This workflow clusters recurring items across the last N phases' LEARNINGS.md files and surfaces promotion candidates to the developer via HITL. No item is promoted without explicit developer approval.

---

## Configuration

Read from project config (`config.json`):

| Key | Default | Description |
|-----|---------|-------------|
| `features.graduation` | `true` | Master on/off switch. `false` skips silently. |
| `features.graduation_window` | `5` | How many prior phases to scan |
| `features.graduation_threshold` | `3` | Minimum cluster size to surface |

---

## Step 1: Guard Checks

```bash
GRADUATION_ENABLED=$(gsd-sdk query config-get features.graduation 2>/dev/null || echo "true")
GRADUATION_WINDOW=$(gsd-sdk query config-get features.graduation_window 2>/dev/null || echo "5")
GRADUATION_THRESHOLD=$(gsd-sdk query config-get features.graduation_threshold 2>/dev/null || echo "3")
```

**Skip silently (print nothing) if:**
- `features.graduation` is `false`
- Fewer than `graduation_threshold` completed prior phases exist (not enough data)

**Skip silently (print nothing) if total items across all LEARNINGS.md files in the window is fewer than 5.**

---

## Step 2: Collect LEARNINGS.md Files

Find LEARNINGS.md files from the last N completed phases (excluding the phase currently completing):

```bash
find .planning/phases -name "*-LEARNINGS.md" | sort | tail -n "$GRADUATION_WINDOW"
```

For each file found:
1. Parse the four category sections: `## Decisions`, `## Lessons`, `## Patterns`, `## Surprises`
2. Extract each `### Item Title` + body as a single item record: `{ category, title, body, source_phase, source_file }`
3. **Skip items that already contain `**Graduated:**`** — they have been promoted and must not re-surface

---

## Step 3: Cluster by Lexical Similarity

For each category independently, cluster items using Jaccard similarity on tokenized title+body:

**Tokenization:** lowercase, strip punctuation, split on whitespace, remove stop words (a, an, the, is, was, in, on, at, to, for, of, and, or, but, with, from, that, this, by, as).

**Jaccard similarity:** `|A ∩ B| / |A ∪ B|` where A and B are token sets. Two items are in the same cluster if similarity ≥ 0.25.

**Clustering algorithm:** single-pass greedy — process items in phase order; add to the first cluster whose centroid (union of all cluster tokens) has similarity ≥ 0.25 with the new item; otherwise start a new cluster.

**Cluster size filter:** only surface clusters with distinct source phases ≥ `graduation_threshold` (not just total items — same item repeated in one phase still counts as 1 distinct phase).

---

## Step 4: Check graduation_backlog in STATE.md

Read `.planning/STATE.md` `graduation_backlog` section (if present). Format:

