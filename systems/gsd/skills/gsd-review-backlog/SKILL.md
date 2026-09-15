---
name: gsd-review-backlog
description: "Use when 999.x backlog items need triage, or the user asks to review, promote, or prune the backlog. Shows each item with its accumulated context, promotes chosen ones into the active milestone, and removes stale ones."
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---


<objective>
Review all 999.x backlog items and optionally promote them into the active
milestone sequence or remove stale entries.
</objective>

<process>

1. **List backlog items:**
   ```bash
   ls -d .planning/phases/999* 2>/dev/null || echo "No backlog items found"
   ```

2. **Read ROADMAP.md** and extract all 999.x phase entries:
   ```bash
   cat .planning/ROADMAP.md
   ```
   Show each backlog item with its description, any accumulated context (CONTEXT.md, RESEARCH.md), and creation date.

3. **Present the list to the user** via AskUserQuestion:
   - For each backlog item, show: phase number, description, accumulated artifacts
   - Options per item: **Promote** (move to active), **Keep** (leave in backlog), **Remove** (delete)

4. **For items to PROMOTE:**
   - Create the phase in the active milestone and capture its number (this creates the
     `.planning/phases/{NEW_NUM}-slug` directory):
     ```bash
     NEW_NUM=$(node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" phase add "${DESCRIPTION}" --raw)
     ```
   - Move the accumulated artifacts from `999.x-slug` into the new directory, then drop the
     now-empty backlog directory:
     ```bash
     mv ".planning/phases/999.x-slug/"* ".planning/phases/${NEW_NUM}-slug/" 2>/dev/null
     rmdir ".planning/phases/999.x-slug" 2>/dev/null
     ```
   - Update ROADMAP.md: move the entry from `## Backlog` section to the active phase list
   - Remove `(BACKLOG)` marker
   - Add appropriate `**Depends on:**` field

5. **For items to REMOVE:**
   - Confirm a second time before deleting, stating that this removes the phase directory
     and its accumulated artifacts recursively:
     ```bash
     rm -rf ".planning/phases/999.x-slug"
     ```
   - Remove the entry from ROADMAP.md `## Backlog` section

6. **Commit changes:**
   ```bash
   node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" commit "docs: review backlog — promoted N, removed M" --files .planning/ROADMAP.md
   ```

7. **Report summary:**
   ```
   ## 📋 Backlog Review Complete

   Promoted: {list of promoted items with new phase numbers}
   Kept: {list of items remaining in backlog}
   Removed: {list of deleted items}
   ```

</process>
