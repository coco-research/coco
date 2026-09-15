# Migration — the SI Team Role roster

What changes for anyone consuming the roster, and what has to change on the consuming
side for the fix to arrive at all.

## The short version

The roster gains fields; the 37 role ids do not change. But **this repository is not
what the tenant reads.** The seed that populates the gallery is not in this repo — no
file here contains `metadata.seed_source`, `persona_prompt` or `team_layer` — so
changing the roster alone fixes nothing downstream until the seeder is pointed at the
new fields. That is the first thing to schedule, not the last.

## Field mapping

| Tenant field (today) | Source of truth (after) | Kept? |
|---|---|---|
| `id` | `id` | unchanged — 37 ids are stable, consumers rely on them |
| `name` | `name` | unchanged |
| `metadata.category` = `"SI Team Roles"` | not role data — this is the catalogue selector | unchanged |
| `metadata.role_name` | — | **retired**, it duplicated `name` |
| top-level `role` | — | **retired**, null on all 37 |
| `description` = `"<Role Name> for the CoCo cross-functional team pipeline."` | `mission` | **replaced** — this was the templated string |
| `metadata.seniority` | `competence.level` | value unchanged (8+/10+/12+/15+/20+), now paired with `competence.meaning` |
| `metadata.team_layer` | `layer` | values unchanged: research / execution / review / synthesis |
| `persona_prompt` | `system_prompt` | byte-for-byte unchanged |
| `resources` (empty on all 37) | `capabilities` + `capability_gaps` | **now populated or explicitly gap-named** |

New fields with no tenant counterpart yet: `family`, `does_not_do`, `inputs`, `outputs`
(including `acceptance_criteria`), `decision_rights`, `handoffs`, `escalation`, `overlap`.

## Why `role` and `metadata.role_name` both go

They are two representations of one fact. `metadata.role_name` duplicates `name`
exactly, and the top-level `role` is null on all 37 — it is a slot someone added and
nobody filled. `name` survives as the single display field, `id` as the single
identifier. A consumer that read either of the retired fields should read `name` and
`id` instead; there is no information loss, because neither carried any.

`category` also survives but is superseded: the roster's `family` is the cluster a role
belongs to (leadership, research, engineering, content, presentation, review), which is
what the overlap rules are keyed on. Keep `category` for back-compat, and add
`metadata.role_family` from `family` — do not overload the catalogue selector with it.

## What the seeder must do

1. Read the roster from `systems/team/roles.yaml` rather than parsing
   `commands/team/roles.md`. The markdown is now generated from that file, so parsing it
   still works, but the YAML is the contract and the markdown is a rendering of it.
2. Write `description` from `mission`. **This is the single change that fixes the
   catalogue**: today the seeder invents the template because the roster has no field it
   could use instead.
3. Write `resources` from `capabilities`; carry `capability_gaps` through as a distinct
   list rather than dropping it, so the catalogue can show "needs a capability this
   framework does not have yet" instead of an indistinguishable empty list.
4. Derive `metadata.role_family` from `family`, and stop writing `metadata.role_name`
   and the top-level `role`.
5. Fail the seed if the roster does not validate:
   `python3 systems/team/validate_roles.py` must exit 0. A seed that cannot see a broken
   roster is how the template survived 37 entries.

## Re-seed required

Yes. Nothing here reaches the tenant until the seed runs again. Two re-seeds have
already overwritten a fix applied downstream, which is why this change is in the roster
and the validator rather than in the catalogue.

## Compatibility

- **37 ids preserved.** No consumer re-pointing is needed.
- **`slide-quality` is merged into `doc-quality`.** The id stays resolvable as a
  deprecated alias; nothing that references it breaks. `doc-quality` now takes the
  artifact type as a parameter.
- `system_prompt` is unchanged for all 37, so anything embedding a persona prompt
  verbatim sees identical text.
- The generated `commands/team/roles.md` keeps its section structure and its
  `- **ID:**` / `- **Layer:**` field lines, so the router in `commands/team/_index.md`
  (which validates `--roles` ids against it, line 68) keeps working unchanged.
