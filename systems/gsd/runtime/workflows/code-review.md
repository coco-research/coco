<purpose>
Review source files changed during a phase for bugs, security issues, and code quality problems. Computes file scope (--files override > SUMMARY.md > git diff fallback), checks config gate, spawns gsd-code-reviewer agent, commits REVIEW.md, and presents results to user. When --fix is passed, delegates to code-review-fix.md after review to auto-apply findings via gsd-code-fixer.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
