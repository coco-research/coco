# Security policy

## Reporting a vulnerability

If you find a security issue in Coco, please **do not** open a public issue.

Instead, report privately:

1. Open a [draft security advisory](https://github.com/rkz91/coco/security/advisories/new) on GitHub, or
2. Email the maintainer directly (contact via GitHub profile)

Include:
- Description of the issue
- Steps to reproduce
- Affected files / skills / adapters
- Impact assessment (what an attacker could do)
- Suggested fix if you have one

## Response

We aim to respond within **7 days** and ship a fix or mitigation within **30 days** for confirmed issues. You'll be credited in the release notes if you wish.

## Scope

Coco is a library of markdown artifacts and shell installers. The most likely security concerns:

| Concern | Severity | Notes |
|---------|----------|-------|
| Malicious skill content (prompt injection) | medium | Skills are markdown; review before installing third-party additions |
| Adapter `install.sh` symlink behavior | low | Symlinks point only into the cloned repo; no privilege escalation |
| Hardcoded credentials | high | Coco ships zero secrets; report any you find immediately |
| Supply-chain via plugin recommendations | low | We link external plugins but don't bundle them |

## Out of scope

- Issues in third-party AI tools (Claude Code, Cursor, Codex, etc.) — report to those projects
- Issues in external plugins listed in `docs/recommended-plugins.md` — report to plugin authors
- Issues in MCP servers — report to https://github.com/modelcontextprotocol/servers

## Disclosure

We follow coordinated disclosure: report → acknowledge → fix → public disclosure. Please give us a reasonable window to ship a fix before publishing details.
