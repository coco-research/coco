<purpose>
Curate sketch design findings and package them into a persistent project skill for future
UI implementation. Reads from `.planning/sketches/`, writes skill to `./.claude/skills/sketch-findings-[project]/`
(project-local) and summary to `.planning/sketches/WRAP-UP-SUMMARY.md`.
Companion to `/gsd:sketch`.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="banner">
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► SKETCH WRAP-UP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
</step>

<step name="gather">
## Gather Sketch Inventory

1. Read `.planning/sketches/MANIFEST.md` for the design direction and reference points
2. Glob `.planning/sketches/*/README.md` and parse YAML frontmatter from each
3. Check if `./.claude/skills/sketch-findings-*/SKILL.md` exists for this project
   - If yes: read its `processed_sketches` list and filter those out
   - If no: all sketches are candidates

If no unprocessed sketches exist:
```
No unprocessed sketches found in `.planning/sketches/`.
Run `/gsd:sketch` first to create design explorations.
```
Exit.

Check `commit_docs` config:
```bash
COMMIT_DOCS=$(gsd-sdk query config-get commit_docs 2>/dev/null || echo "true")
```
</step>

<step name="curate">
## Curate Sketches One-at-a-Time

Present each unprocessed sketch in ascending order. For each sketch, show:

- **Sketch number and name**
- **Design question:** from frontmatter
- **Winner:** which variant was selected (if any)
- **Tags:** from frontmatter
- **Key decisions:** summarize what was decided visually
