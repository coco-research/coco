# Codex CLI engineering — Pragmatic Engineer (2026-02-17)

Source: https://newsletter.pragmaticengineer.com/p/how-codex-is-built
Companion: https://developers.openai.com/codex/cli

## Origin story
- Greg Brockman and Sam Altman shared conviction: "Eventually, we should have an autonomous software engineer working alongside us"
- The capabilities from o1-preview made them feel the time was now to dedicate a group to it
- Set as 2025 company goal: an agentic software engineer by year-end (confirmed in Latent Space interview)

## Team
- **Thibault Sottiaux (Tibo)** — Head of Codex
- **Michael Bolin** — Tech lead, open source repo
- **Gabriel Peal** — VS Code extension + Codex desktop app foundations
- **Fouad Matin** — Led CLI release; oversees safety and security

## Technical choices
- Rust over TypeScript and Go — for performance, memory safety, correctness, minimal npm dependency surface, multi-environment deployability
- Open source from day one

## Recursive scaling
- Codex generates >90% of its own codebase
- Engineers function as "agent managers" running 4–8 parallel agents simultaneously
- Used for feature implementation, code review, and security audits

## Brockman's tweet on launch week (October 2025, X/@gdb)
"This has one of the most exciting launch weeks in OpenAI's history, with a goal of making agents more real, useful, and accessible for all our users. codex can now smartly do much more on your computer, remember more of your context, and run more ongoing work independently."
Source: https://x.com/gdb/status/2047757455606903178

## Brockman tweet on local + remote convergence
"Codex CLI keeps getting better. In the long run, I expect that 'local' (e.g. Codex CLI) and 'remote' (e.g. Codex) coding agents will come together — imagine their combination as a remote coworker who can also look over your shoulder. Excited for the future of programming!"
Source: https://x.com/gdb/status/1923492615959478375

## Brockman tweet on app server
"build your own agents with codex app-server"
Source: https://x.com/gdb/status/2049609076351381580
