# The analysis taxonomy

The exploration stage writes `.arch/ANALYSIS.md` against the fixed seven-section
skeleton below. The skeleton is fixed on purpose: a free-form analysis produces a
different shape every run, which makes the downstream synthesis stage improvise, and
improvised structure is what makes generated architecture documents unreviewable.

This file is used only on the fallback path. When `.planning/codebase/` exists,
`gsd-map-codebase` has already produced seven structured documents that cover the same
ground in more depth, and the exploration stage is skipped entirely rather than
duplicated.

## Why the analysis and the index are separate stages

The exploration stage may use tools and writes prose. The synthesis stage may not use
tools and writes schema-shaped JSON. Separating them is the single most effective
structural choice in the upstream design, for two reasons.

Structured output stays clean when the model producing it is not simultaneously
deciding what to explore. A model that is both crawling and formatting will drift out
of schema under context pressure.

The prose report is cacheable. It is pinned to a commit, so re-rendering the index
after a schema change or a review finding costs one cheap non-exploring call rather
than a full re-crawl.

## The seven sections

Every section is required. A section with nothing to report says so in one sentence
rather than being omitted, because an absent section is indistinguishable from an
overlooked one.

**1. Executive summary.** Two or three sentences describing what this system does and
the shape of its architecture.

**2. Tech stack.** Every technology with the purpose it serves, grouped by concern:
the user-facing layer, the service layer, persistence, identity, and infrastructure.
Name the technology and what it is used *for*, never the technology alone.

**3. Architecture overview.** How the system is organised: the directory philosophy,
the module organisation pattern, and the dominant data-flow patterns.

**4. Core components.** Each major component with its name, purpose, dependencies, and
how it communicates with the others. This section feeds the index most directly, so
the component boundaries chosen here should already satisfy the rules in
`component-rules.md`.

**5. Data flow.** How data moves: entry points inward, persistence interactions, and
outbound calls to external systems.

**6. External integrations.** Every third-party service, what it provides, and how it
is wired in.

**7. Key architectural decisions.** Notable patterns and choices, including the ones
that look unusual and turn out to be deliberate.

## Constraints

**Ten thousand characters, total.** The cap is a forcing function. An analysis that
does not fit is describing implementation rather than architecture.

**Every claim is backed by evidence from the codebase.** Cite the path that supports
the claim. A claim that cannot be pointed at a file does not belong in the report,
because the index built from it will inherit the invention.

**Specific and technical, never generic.** "Uses a queue for background work" is not a
finding. "Background jobs run through Inngest with each step separately retryable,
defined in `src/inngest/functions.ts`" is.

**Describe what exists.** Not what should exist, not what would be better, not what is
missing. Recommendations belong in a review, and the index that consumes this report is
reverse-only.

## Where truncation matters

`repo_tree.py` reports whether the tree it produced was truncated. If it was, say so at
the top of the analysis in those words. A truncated tree means whole regions of the
repository were never visible, and the downstream reconciliation algorithm treats the
tree as the source of truth — so an unflagged truncation causes real components to be
deleted as though their code had been removed. Upstream captured this flag and never
read it in any caller, which is the most consequential defect in the design this skill
draws on.

---

## Attribution

Adapted from devildev by lak7, Apache-2.0, <https://github.com/lak7/devildev>,
`actions/reverse-architecture.ts` lines 771 to 805 ("OUTPUT FORMAT" and "CRITICAL
CONSTRAINTS"). The seven-section skeleton, the ten-thousand-character cap, and the
evidence constraint are substantially upstream.

Modifications, per Apache-2.0 § 4(b):

- The requirement that an empty section state its emptiness rather than be omitted is
  new, because an omitted section cannot be distinguished from an oversight.
- The instruction to declare tree truncation at the top of the report is new. Upstream
  computed the flag and no caller ever read it.
- Upstream's framing of the analysis as input to a *diagram* was changed to input to a
  structural *index*, since presentation fields are not carried across at all.
