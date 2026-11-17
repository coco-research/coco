'use strict';

/**
 * Typed flag parser for the /gsd:code-review command.
 *
 * This is the canonical IR for code-review argument parsing. The workflow
 * (code-review.md) delegates flag dispatch logic to this module so that:
 *  1. Tests assert on a structured IR rather than on rendered bash text.
 *  2. The dispatch decision is testable without instantiating the workflow.
 *
 * @typedef {Object} CodeReviewFlags
 * @property {boolean} fix   - true when --fix is present in argv
 * @property {boolean} all   - true when --all is present in argv (implies fix)
 * @property {boolean} auto  - true when --auto is present in argv (implies fix)
 * @property {string}  depth - depth override value, or '' if not supplied
