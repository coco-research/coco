# Coco vs alternatives

Honest comparison. Helps you decide whether to switch.

| Capability | Coco | Continue | Cline | Cursor (built-in) | LangChain |
|---|---|---|---|---|---|
| **Format** | Markdown + frontmatter | Custom YAML config | Markdown rules | Cursor rules `.mdc` | Python / TS code |
| **Skills (curated)** | 59 (+74 in bundles) | community marketplace | examples in repo | starter set | none (you build) |
| **Slash commands** | 34 namespaced | yes (custom commands) | yes (custom modes) | yes (rules-as-commands) | n/a |
| **Subagents** | 10 + 24 in GSD | no | no | no | yes (chains/agents) |
| **Multi-agent orchestration** | yes (`/team:ship`, GSD waves) | no | no | no | yes (LangGraph) |
| **Project state persistence** | yes (`.planning/`, atomic commits) | no | no | no | yes (memory modules) |
| **Verification gates before "done"** | yes (auto-run build/lint/test) | no | no | no | manual |
| **Cross-IDE portability** | yes (4 stable adapters) | VS Code only | VS Code/JetBrains | Cursor only | any (you wrap) |
| **AGENTS.md compatible** | yes | no | partial | no | n/a |
| **Cost** | $0 | $0 | $0 | Cursor sub | $0 framework |
| **Telemetry** | none | opt-out | none | yes | none (you control) |
| **Onboarding time** | 90 seconds (`bash install.sh`) | extension install + config | extension install | built-in | days (build it) |
| **Self-contained vs framework** | self-contained library | framework | extension | proprietary | framework |
| **Best for** | Anyone wanting a curated, portable, multi-agent toolkit | VS Code users wanting custom commands | VS Code/JetBrains users wanting rules + custom modes | Cursor users staying in Cursor | Engineers building agent apps from scratch |

## When to pick what

**Pick Coco if:**
- You use multiple AI tools and want skills that follow you
- You want orchestration (`/team:ship`, GSD), not just code completion
- You want state that survives `/clear` and context resets
- You want built-in verification before claiming "done"
- You want a curated library, not a blank slate

**Pick Continue if:**
- You're VS Code-only and want a customizable AI extension with model switching
- You want a marketplace ecosystem of community skills (broader than Coco)

**Pick Cline if:**
- You want a VS Code extension with custom modes / rules
- You like the agent-in-IDE experience that runs commands directly

**Pick Cursor's built-in if:**
- You're a Cursor power user and want maximum native integration
- You don't need cross-IDE portability

**Pick LangChain if:**
- You're building an AI app from scratch, not augmenting your IDE
- You need full programmatic control over chains, retrievers, agents
- You're willing to write Python/TS, not markdown

## Can you use Coco WITH them?

Yes. Coco is markdown — non-conflicting. Run Coco alongside Continue/Cline; the AI tool sees both. LangChain is a different layer (app framework, not IDE skills) — Coco extends your IDE; LangChain builds your app.

## Why Coco isn't trying to be them

Coco is intentionally not a marketplace, not a framework, and not a chat extension. It's a curated library. Strong opinions on what's worth doing well, packaged once, runnable anywhere. If you want a marketplace, install Continue. If you want a framework, use LangChain. If you want a single curated toolkit that works across tools, install Coco.

## Honest limitations

- Coco doesn't have a marketplace (yet). All skills are in this one repo.
- No auto-update mechanism beyond `git pull && bash install.sh`
- No web UI / GUI — pure CLI + IDE adapters
- VS Code adapter (Continue-based) planned for v0.2 — not stable yet
- Antigravity adapter planned for v0.2 — not stable yet
- No telemetry means we can't tell which skills are most-used (and we like it that way)
