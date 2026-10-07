# AGENTS.md — read this before touching anything

## Repo

- **Name:** `coco`
- **Origin:** `https://github.com/coco-research/coco.git`
- **Stack:** node
- **SoT playbook:** `~/code/jev-use/docs/repo-playbook.html`

## 0. The documents, and when each is authoritative

| File | Answers | Update when |
| --- | --- | --- |
| `docs/prd.md` | What and why | Scope changes |
| `docs/architecture.md` | How the parts fit | Structure changes |
| `docs/rules.md` | The laws. Invariants | ONLY with owner approval |
| `docs/design.md` | What it looks and feels like | UI work |
| `docs/tasks.md` | What is worked on now | Every PR |
| `docs/memory.md` | Decisions and dead ends | Every PR that settles something |

If two documents disagree, the earlier one in that table wins. Never
silently pick one — fix the disagreement in the same PR.

## 1. The PR contract

- Every change is a small PR. No direct pushes to `main`.
- Gate green before review. Run `.githooks/pre-push` or `git push` and let it.
- Evidence, not assertions. Paste the command and its real output.
- One concern per PR. Two things touched means two PRs.
- Fill the PR template in honestly, including the Risk section.

## 2. Never commit

- Any API key, token, or secret. Not in code, not in docs, not in a fixture.
- Absolute personal paths in shipped code. Docs may name one as an example.
- Build output. `target/`, `dist/`, `node_modules/` are ignored and stay ignored.

## 3. When unsure

`docs/rules.md` holds the invariants, each with the measurement that justifies it.
If a task appears to require breaking one, stop and ask.

## 4. Recording what you learned

`docs/memory.md` is not a diary. It records decisions with reasons and
dead ends worth not repeating. If you spent an hour proving a
hypothesis wrong, that sentence saves the next agent the hour.
## 5. A bug you find is a bug you fix

Found a bug while installing or working in this repo? Fix it and open a PR. A finding left in a chat is lost.

- **Counts as a bug:** an install that delivers less than it advertises; a path, count, command or skill reference that does not resolve; a gate that cannot fail; a silent fallback where a loud failure belongs; docs that contradict the code.
- **How:** reproduce in a throwaway `HOME` first. Fix the source, not generated output. Add the gate that would have caught it. Run the full `ci.yml` mirror, including `build-delivery-index.py`, before pushing. The PR says what broke, why it was invisible, and the command that proves the fix.
- **Scope:** this repo, fix and PR. Any other repo, report to its owner and stop.
