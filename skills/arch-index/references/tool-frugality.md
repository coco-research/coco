# The tool-frugality protocol

This protocol bounds how much of a repository the exploration stage reads. It applies
only on the fallback path, when neither a `.planning/codebase/` map nor a gitnexus
index is available and the skill must crawl the repository itself.

The reason to bound it is not cost alone. An agent that reads two hundred files
arrives at the synthesis stage with a context window full of implementation detail and
produces a component map that describes files rather than capabilities. Reading less
produces a better index, not merely a cheaper one.

## The core claim

The dependency manifest and the directory tree together answer most of the
architectural questions. The manifest tells you the stack. The directory layout tells
you the organising principle. File names in the tree tell you where responsibilities
sit. Roughly seventy to eighty percent of what the index needs is available before a
single file is opened.

## Three phases

**Phase 1 — inference, with no file reads at all.** Extract everything obtainable from
the dependency manifest, the compact tree emitted by `repo_tree.py`, and the root
directory listing. Identify the stack, the framework conventions in use, the module
organisation, and the likely component boundaries. Do not open a file during this
phase. This phase should answer most of the questions.

**Phase 2 — targeted reads, at most five to eight files.** Only for a critical unknown
that directly changes the component map. Legitimate reads are the ones whose contents
cannot be inferred from their existence: a schema definition, a routing or dependency
injection root, a configuration file that redirects the whole build, an entry point
whose imports reveal the layering. Prefer Grep over Read when confirming that a
pattern exists, because Grep returns the matching lines and a read returns the whole
file.

**Phase 3 — synthesis.** Combine the findings. No further reads.

## The pre-call self-check

Before every file read, answer one question: *can I infer this from what I already
have?* If the answer is yes, do not read the file. This single question removes most
wasted reads, because the usual failure is opening a file to confirm something the
directory structure already established.

## Never read these

Reading these costs tokens and changes no architectural conclusion:

- `README.md`, `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`, and other prose
- Lock files and generated files of every kind
- Test files, unless the question is specifically about the testing architecture
- Individual leaf components or single-purpose modules, whose role is evident from
  their path
- Anything already pruned by `repo_tree.py`, which will not appear in the tree at all

## Prefer search over read

When the question is "does this pattern exist here", Grep answers it and returns the
matching lines. When the question is "how does this work end to end", a read is
warranted. Upstream's version of this rule recommended its own code-search tool over
its file-read tool, but that search returned only paths and relevance scores and could
therefore not confirm anything about content. Grep returns the matched lines, so the
rule is stronger here than it was upstream.

## This budget is not mechanically enforced

There is no transcript API available to a caller, and the reads happen inside a
subagent whose trace the caller never sees. The read budget is therefore
prose-enforced guidance, and no artifact produced by this skill may report it as a
verified constraint. `team:architecture.md` lists it explicitly among the rules that
carry no exit code. Stating this plainly is the point: a budget presented as enforced
when it is not is exactly the kind of claim this skill exists to eliminate.

---

## Attribution

Adapted from devildev by lak7, Apache-2.0, <https://github.com/lak7/devildev>,
`actions/reverse-architecture.ts` lines 715 to 749 ("CRITICAL - TOKEN EFFICIENCY
RULES" and "ANALYSIS APPROACH"). The three-phase structure, the five-to-eight read
ceiling, the never-read list, and the pre-call self-check question are substantially
upstream.

Modifications, per Apache-2.0 § 4(b):

- The framework-specific questions in upstream's analysis section ("Is this App Router
  or Pages Router?") were removed, because they restrict the protocol to a single
  JavaScript framework. The phases are now ecosystem-neutral.
- Upstream's "prefer searchCode over getFileContent" rule was rewritten, because
  upstream's search returned only paths and relevance scores and therefore could not
  confirm a pattern's existence. Grep can.
- The closing statement that the budget is not mechanically enforced is new. Upstream
  presented the ceiling as a hard rule with no means of checking it.
