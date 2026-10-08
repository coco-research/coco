# Third-party licence notices

MIT and Apache-2.0 require the original copyright and permission notice to travel with every copy. These files are the upstream LICENSE texts, copied byte for byte from each project's repository (the commit noted below, fetched 2026-10-06). They cover the CoCo files listed beside them. Licences that already sit inside a vendored folder (for example `systems/gsd/LICENSE`, `systems/hyperframes/LICENSE`, `skills/humanizer/LICENSE`) are not repeated here.

| File | Upstream | Covers in this repository |
|---|---|---|
| `superpowers.LICENSE` | [obra/superpowers](https://github.com/obra/superpowers) @ 8ca22dba9a94, MIT, Copyright (c) 2025 Jesse Vincent | `skills/brainstorming`, `skills/dispatching-parallel-agents`, `skills/executing-plans`, `skills/finishing-a-development-branch`, `skills/receiving-code-review`, `skills/requesting-code-review`, `skills/subagent-driven-development`, `skills/systematic-debugging`, `skills/test-driven-development`, `skills/using-git-worktrees`, `skills/using-superpowers`, `skills/verification-before-completion`, `skills/writing-plans`, `skills/writing-skills` |
| `taste-skill.LICENSE` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) @ ce26fc25c0e5, MIT, Copyright (c) 2026 Leonxlnx | `skills/design-taste-frontend`, `skills/redesign-existing-projects` |
| `web-interface-guidelines.LICENSE` | [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) @ 434b7f913646, MIT, Copyright (c) 2025 Vercel Labs | `skills/web-design-guidelines` |
| `ai-website-cloner-template.LICENSE` | [JCodesMore/ai-website-cloner-template](https://github.com/JCodesMore/ai-website-cloner-template) @ ee3f5a2f31fd, MIT, Copyright (c) 2025 JCodesMore | `skills/clone-website` (its structure) |

Not covered here: `skills/voice-ai`, `skills/prd-mastery` and `skills/karpathy-guidelines` have no upstream LICENSE file or copyright notice to copy (the prd-mastery and karpathy-guidelines upstreams only say "MIT" in their README), so Coco ships each only as a link-only stub with no upstream text. `skills/vercel-react-best-practices` (vercel-labs/agent-skills: MIT declared in its README and SKILL.md frontmatter, but no LICENSE file or copyright notice) becomes a link-only stub in #333. See the lab-0062 held-items status in `CREDITS.md`.
