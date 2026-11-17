'use strict';

const { PHASE_SUBCOMMANDS } = require('./command-aliases.generated.cjs');
const { output } = require('./core.cjs');

// ─── SDK bridge (Phase 6) — shared loader via cjs-sdk-bridge.cjs ──────────────
const { tryLoadSdk, getExecuteForCjs } = require('./cjs-sdk-bridge.cjs');

// ─── CommandRoutingHub (issue #3788) ──────────────────────────────────────────
const { createHub, ERROR_KINDS } = require('./command-routing-hub.cjs');

/**
 * Manifest-backed phase subcommand router.
 * Keeps gsd-tools.cjs thin while preserving existing command semantics.
 *
 * Phase 6: all CJS-handled phase subcommands are dispatched via executeForCjs
 * when the SDK is available. CJS fallback retained when:
 * - GSD_WORKSTREAM is active (workstream-scoped requests fall through to CJS).
 * - SDK is unavailable (build not present).
 *
 * SDK-only (unsupported in CJS router):
 * - list-plans: SDK-only.
 * - list-artifacts: SDK-only.
 * - scaffold: routed through top-level scaffold command.
 *
 * CJS-only subcommands: none.
 *
 * #3788: dispatch is now mediated by CommandRoutingHub. The public entry point
 * and observable CLI behaviour are unchanged.
 */
function routePhaseCommand({ phase, args, cwd, raw, error }) {
  const activeWorkstream = process.env.GSD_WORKSTREAM;
  const sdkAvailable = !activeWorkstream && tryLoadSdk();

  // ── Unsupported / SDK-only subcommands ─────────────────────────────────────
  // Resolved before dispatch so the error message matches the pre-#3788 text.
  const UNSUPPORTED = {
    'list-plans': 'phase list-plans is SDK-only. Use: gsd-sdk query phase.list-plans ...',
    'list-artifacts': 'phase list-artifacts is SDK-only. Use: gsd-sdk query phase.list-artifacts ...',
    scaffold: 'phase scaffold is routed through the top-level scaffold command.',
  };

  const subcommand = args[1];

  if (subcommand && UNSUPPORTED[subcommand]) {
    error(UNSUPPORTED[subcommand]);
    return;
  }

  // ── No subcommand → reject early with helpful error ────────────────────────
  // Pre-#3788 code resolved unknown subcommands via routeCjsCommandFamily which
  // fell through to error() when no handler matched (including undefined).
  // Post-#3788 the hub's manifest check is skipped for falsy subcommand, so we
  // must guard here to preserve the deterministic "Available: ..." error message.
  if (!subcommand) {
    const available = PHASE_SUBCOMMANDS.filter(s => !UNSUPPORTED[s]).join(', ');
    error(`Unknown phase subcommand. Available: ${available}`);
    return;
  }

  // ── CJS-only subcommands (always bypass SDK path) ──────────────────────────
