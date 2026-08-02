# Component rules

These rules decide what becomes a component, what it is called, and how many there
are. They are the substance of the index; the schema in `schema.md` is only its shape.

## What qualifies as a component

Four tests, all of which must pass.

**Runtime only.** A component exists while the system is running. Build tooling,
package managers, bundlers, linters, test frameworks, deployment platforms, content
delivery networks, and static asset directories are excluded. They are real and they
matter, and they are not components.

**Business capability plus technical clarity.** You must be able to say both what the
component does in the language of the business and how it does it in the language of
the implementation. If only one of those is available, the boundary is wrong.

**Independently replaceable.** The component has a distinct responsibility that could
be swapped out on its own. If two candidate components cannot be replaced separately,
they are one component.

**Evidence-based.** The component is visible in the analysis and its code is on disk.
There are no recommended, suggested, optional, or planned components. This test is the
one the validator enforces mechanically, through check 5 on path existence and check 10
on aspirational titles.

## How many

| System shape | Components |
|---|---|
| Simple — basic persistence, a single user-facing surface | 3 to 4 |
| Medium — identity, payments, several distinct features | 4 to 6 |
| Complex — multiple services, several external integrations | 6 to 8 |

Check 2 enforces the outer bounds of three and eight. Fewer, well-defined components
beat many granular ones every time; the failure mode in practice is always
over-decomposition, never under-decomposition.

A monorepo with dozens of packages does not fit this ladder. Version 1.0 of the
contract does not solve that. The eventual answer is one index per workspace package
plus a root index whose components are the packages, and it is explicitly out of scope.

## How to group

Combine technologies that serve the same business goal rather than splitting by vendor
or by language.

- All the user-facing code, whatever its framework, is usually one component.
- All the request-handling and business-rule code is usually one component.
- A datastore together with its cache and search index is one data component, if they
  all exist.
- External services group by the function they provide, not by the company that
  provides them.

## Naming

The formula is `[Business Function] + [Implementation Context]`, and it bans failure in
two directions at once. This two-sided calibration is the highest-leverage part of the
upstream design.

| Too technical | Too vague | Right |
|---|---|---|
| `Next.js App Router` | `Customer System` | `Customer Web Application` |
| `Node.js Backend` | `Business Logic` | `Product Management API` |
| `PostgreSQL Database` | `Data Platform` | `User Data Repository` |
| `Stripe Service` | `Payments` | `Payment Processing Integration` |

Check 10 rejects aspirational titles and check 11 rejects titles naming pure
infrastructure. Whether a title is too *vague* is not mechanically checkable and is a
Layer 3 review judgement.

Connections are named for what flows across them in business terms. `Customer Orders`,
not `POST /api/orders`. `User Authentication`, not `JWT validation`.

## Purpose statements

The formula is `[Business capability] delivered through [technical approach]; [key
implementation detail]`.

Good, because both halves are present:

> Manages customer accounts and order history through a web interface; synchronises
> data with SWR and revalidates on focus.

> Stores and retrieves business data in PostgreSQL; uses Prisma for type-safe queries
> and keeps migrations in version control.

Bad, and why:

> Handles UI rendering and client-side logic.

Purely technical, with no business context — it describes a layer, not a capability.

> Manages customer relationships.

Purely business, with no technical context — it could describe a spreadsheet.

## Anti-patterns

Never create a component for any of these:

- **Infrastructure** — build systems, hosting platforms, content delivery networks,
  deployment tooling
- **File system artifacts** — public folders, asset directories, build output
- **Development tooling** — package managers, bundlers, linters, test frameworks
- **Purely technical names** — see the naming table above
- **Vague business names** — see the naming table above
- **Implementation details** — individual libraries, specific endpoints, database
  tables
- **Hypothetical components** — anything not evident in the analysis and on disk

## Merging and pruning across rebuilds

Component identifiers are stable and survive rebuilds. When re-mapping an existing
index, the current file tree is the source of truth and the deletion-first rule
decides each component's fate:

| Surviving primary paths | Verdict | Action |
|---|---|---|
| None | `REMOVE` | Delete the component and every connection to it |
| Some | `PRUNE` | Remove the dead paths, keep the component and its identifier |
| All | `KEEP` | No change |

`arch_drift.py` computes these verdicts deterministically, and the synthesis stage
applies them as settled fact rather than re-deciding them.

**A component is never preserved for historical reasons.** This is the rule that every
keep-the-documentation-in-sync system actually violates, and violating it is how an
index accumulates components describing code that was deleted two years ago. If the
code is gone, the component is gone.

The one exception is procedural rather than sentimental: if the file tree was
truncated, no reconciliation runs at all, because absence of evidence in a partial tree
is not evidence of deletion.

---

## Attribution

Adapted from devildev by lak7, Apache-2.0, <https://github.com/lak7/devildev>:
`prompts/ReverseArchitecture.ts` lines 278 to 371 (component creation rules, the
component-count ladder, the grouping strategy, the naming formula and its worked
examples, and the purpose-statement formula), lines 493 to 507 (the anti-pattern list),
and lines 578 to 641 (deletion-first reconciliation). Also
`prompts/dev/architecture.ts` lines 15 to 42.

Modifications, per Apache-2.0 § 4(b):

- Numeric confidence bands and the third ownership tier were dropped, because nothing
  in this system reads either one.
- The worked naming examples were rewritten into a three-column table so that the
  too-technical and too-vague failures sit beside the correct form. Upstream listed the
  two failure modes in separate paragraphs, which loses the calibration.
- Framework-specific examples were generalised, since the index is not restricted to
  JavaScript projects.
- The deletion-first table gained the truncated-tree exception, which upstream lacked;
  upstream computed a truncation flag, never read it, and would therefore delete real
  components when the tree was partial.
