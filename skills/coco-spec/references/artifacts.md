# Artifact templates

Section lists for the four files under `docs/specs/<feature>/`. Keep the headings. Write sentences where a sentence will do, and never leave a section blank.

## prd.md

1. **Intent.** One paragraph: the problem, for whom, and what gets better.
2. **In scope / out of scope.** Two lists. Out of scope is required, and should name the tempting neighbour.
3. **User stories.** Seven at most, each "as a ..., I want ..., so that ...".
4. **Requirements.** Numbered and testable. If it cannot fail a check, it is not a requirement.
5. **Success check.** The command or observation that proves it works.
6. **Open questions.** None may stay open at sign-off. Move each answer up into the sections above.

## arch.md

0. **Diagram.** `arch-diagram.html`, required. Real HTML or SVG, with the current state and the change in one picture. A fenced block of ASCII art is not a diagram.
1. **Current state.** How it works today, with `file:line` for each claim.
2. **Change.** What moves, what is added, what is deleted.
3. **Files and symbols.** Exact paths, and the functions or types that change.
4. **Data and APIs.** New or changed shapes, storage, endpoints, events.
5. **Risks.** Each with a way to notice it went wrong.
6. **Test surface.** What the tests reach, and what they cannot.

## plan.md

Numbered tasks, starting at 1. Each task has:

- **Files.** Create, modify (with line ranges), test.
- **Test.** The command that fails before and passes after.
- **Done when.** The observable result, not "the code is written".
- **Size.** One task is one PR, under 800 lines.

A task with two "and then"s is two tasks. The first tasks are the working set. Later tasks may change after the first build, and a changed plan is signed again.

## build-log.md

One heading per task, in the order they were built.

- **Command.** What ran.
- **Result.** Pass or fail, with the real output line.
- **Files changed.** Paths, not descriptions.
- **Note.** Only when something surprised you, or a task was split.

A task is not done until its heading exists.
