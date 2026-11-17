# Import Workflow

External plan ingestion with conflict detection and agent delegation.

- **--from**: Import external plan → conflict detection → write PLAN.md → validate via gsd-plan-checker

Future: `--prd` mode (PRD extraction into PROJECT.md + REQUIREMENTS.md + ROADMAP.md) is planned for a follow-up PR.

---

<step name="banner">

Display the stage banner:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► IMPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

</step>

<step name="parse_arguments">

Parse `$ARGUMENTS` to determine the execution mode:

- If `--from` is present: extract FILEPATH (the next token after `--from`), set MODE=plan
- If `--prd` is present: display message that `--prd` is not yet implemented and exit:
  ```
  GSD > --prd mode is planned for a future release. Use --from to import plan files.
  ```
- If neither flag is found: display usage and exit:

```
Usage: /gsd:import --from <path>

  --from <path>   Import an external plan file into GSD format
```

**Validate the file path:**

Verify the path does not contain traversal sequences and the file exists:

```bash
case "{FILEPATH}" in
  *..* ) echo "SECURITY_ERROR: path contains traversal sequence"; exit 1 ;;
esac
test -f "{FILEPATH}" || echo "FILE_NOT_FOUND"
```

If FILE_NOT_FOUND: display error and exit:

```
╔══════════════════════════════════════════════════════════════╗
║  ERROR                                                       ║
╚══════════════════════════════════════════════════════════════╝

File not found: {FILEPATH}

**To fix:** Verify the file path and try again.
```

</step>

---

## Path A: MODE=plan (--from)

<step name="plan_load_context">

Load project context for conflict detection:

1. Read `.planning/ROADMAP.md` — extract phase structure, phase numbers, dependencies
2. Read `.planning/PROJECT.md` — extract project constraints, tech stack, scope boundaries.
   **If PROJECT.md does not exist:** skip constraint checks that rely on it and display:
   ```
   GSD > Note: No PROJECT.md found. Conflict checks against project constraints will be skipped.
   ```
3. Read `.planning/REQUIREMENTS.md` — extract existing requirements for overlap and contradiction checks.
   **If REQUIREMENTS.md does not exist:** skip requirement conflict checks and continue.
4. Glob for all CONTEXT.md files across phase directories:
   ```bash
   find .planning/phases/ -name "*-CONTEXT.md" -o -name "CONTEXT.md" 2>/dev/null
   ```
   Read each CONTEXT.md found — extract locked decisions (any decision in a `<decisions>` block)

Store loaded context for conflict detection in the next step.

</step>

<step name="plan_read_input">

Read the imported file at FILEPATH.

Determine the format:
- **GSD PLAN.md format**: Has YAML frontmatter with `phase:`, `plan:`, `type:` fields
- **Freeform document**: Any other format (markdown spec, design doc, task list, etc.)
