'use strict';

/**
 * GENERATED FILE — state.*, verify.*, init.*, phase.*, phases.*, validate.*, roadmap.*, and non-family alias/subcommand metadata for CJS routing.
 * Source: sdk/src/query/command-manifest.{state,verify,init,phase,phases,validate,roadmap,non-family}.ts
 */

const STATE_COMMAND_ALIASES = [
  {
    "canonical": "state.load",
    "aliases": [],
    "subcommand": "load",
    "mutation": false
  },
  {
    "canonical": "state.json",
    "aliases": [
      "state json"
    ],
    "subcommand": "json",
    "mutation": false
  },
  {
    "canonical": "state.get",
    "aliases": [
      "state get"
    ],
    "subcommand": "get",
    "mutation": false
  },
  {
    "canonical": "state.update",
    "aliases": [
      "state update"
    ],
    "subcommand": "update",
    "mutation": true
  },
  {
    "canonical": "state.patch",
    "aliases": [
      "state patch"
    ],
    "subcommand": "patch",
    "mutation": true
  },
  {
    "canonical": "state.begin-phase",
    "aliases": [
      "state begin-phase"
    ],
    "subcommand": "begin-phase",
    "mutation": true
  },
  {
    "canonical": "state.advance-plan",
    "aliases": [
      "state advance-plan"
    ],
    "subcommand": "advance-plan",
    "mutation": true
  },
  {
    "canonical": "state.record-metric",
    "aliases": [
      "state record-metric"
    ],
    "subcommand": "record-metric",
    "mutation": true
  },
  {
    "canonical": "state.update-progress",
    "aliases": [
      "state update-progress"
    ],
    "subcommand": "update-progress",
    "mutation": true
  },
  {
    "canonical": "state.add-decision",
    "aliases": [
      "state add-decision"
    ],
    "subcommand": "add-decision",
    "mutation": true
  },
  {
    "canonical": "state.add-blocker",
    "aliases": [
      "state add-blocker"
    ],
    "subcommand": "add-blocker",
    "mutation": true
  },
  {
    "canonical": "state.resolve-blocker",
    "aliases": [
      "state resolve-blocker"
    ],
    "subcommand": "resolve-blocker",
    "mutation": true
  },
  {
    "canonical": "state.record-session",
    "aliases": [
      "state record-session"
    ],
    "subcommand": "record-session",
    "mutation": true
  },
  {
    "canonical": "state.signal-waiting",
    "aliases": [
      "state signal-waiting"
    ],
    "subcommand": "signal-waiting",
    "mutation": true
  },
  {
    "canonical": "state.signal-resume",
    "aliases": [
      "state signal-resume"
    ],
    "subcommand": "signal-resume",
    "mutation": true
  },
  {
    "canonical": "state.planned-phase",
    "aliases": [
      "state planned-phase"
    ],
    "subcommand": "planned-phase",
    "mutation": true
  },
  {
    "canonical": "state.validate",
    "aliases": [
      "state validate"
    ],
    "subcommand": "validate",
    "mutation": false
  },
  {
    "canonical": "state.sync",
    "aliases": [
      "state sync"
    ],
    "subcommand": "sync",
    "mutation": true
  },
  {
    "canonical": "state.prune",
    "aliases": [
      "state prune"
    ],
    "subcommand": "prune",
    "mutation": true
  },
  {
    "canonical": "state.milestone-switch",
    "aliases": [
      "state milestone-switch"
    ],
    "subcommand": "milestone-switch",
    "mutation": true
  },
  {
    "canonical": "state.add-roadmap-evolution",
    "aliases": [
      "state add-roadmap-evolution"
    ],
    "subcommand": "add-roadmap-evolution",
    "mutation": true
  }
];

const VERIFY_COMMAND_ALIASES = [
  {
    "canonical": "verify.plan-structure",
    "aliases": [
      "verify plan-structure"
    ],
    "subcommand": "plan-structure",
    "mutation": false
  },
  {
    "canonical": "verify.phase-completeness",
    "aliases": [
      "verify phase-completeness"
    ],
    "subcommand": "phase-completeness",
    "mutation": false
  },
  {
    "canonical": "verify.references",
    "aliases": [
      "verify references"
    ],
    "subcommand": "references",
    "mutation": false
  },
  {
    "canonical": "verify.commits",
    "aliases": [
      "verify commits"
    ],
    "subcommand": "commits",
    "mutation": false
  },
  {
    "canonical": "verify.artifacts",
    "aliases": [
      "verify artifacts"
    ],
    "subcommand": "artifacts",
    "mutation": false
  },
  {
    "canonical": "verify.key-links",
    "aliases": [
      "verify key-links"
    ],
    "subcommand": "key-links",
    "mutation": false
  },
  {
    "canonical": "verify.schema-drift",
    "aliases": [
      "verify schema-drift"
    ],
    "subcommand": "schema-drift",
    "mutation": false
  }
];

const INIT_COMMAND_ALIASES = [
  {
    "canonical": "init.execute-phase",
    "aliases": [
      "init execute-phase"
    ],
    "subcommand": "execute-phase",
    "mutation": false
  },
  {
    "canonical": "init.plan-phase",
    "aliases": [
      "init plan-phase"
    ],
    "subcommand": "plan-phase",
    "mutation": false
  },
  {
    "canonical": "init.new-project",
    "aliases": [
      "init new-project"
    ],
    "subcommand": "new-project",
    "mutation": false
  },
  {
    "canonical": "init.new-milestone",
    "aliases": [
      "init new-milestone"
    ],
    "subcommand": "new-milestone",
    "mutation": false
  },
  {
    "canonical": "init.quick",
    "aliases": [
      "init quick"
    ],
    "subcommand": "quick",
    "mutation": false
  },
  {
    "canonical": "init.ingest-docs",
    "aliases": [
      "init ingest-docs"
    ],
    "subcommand": "ingest-docs",
    "mutation": false
  },
  {
    "canonical": "init.resume",
    "aliases": [
      "init resume"
    ],
    "subcommand": "resume",
    "mutation": false
