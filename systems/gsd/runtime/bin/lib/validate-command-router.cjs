'use strict';

const { VALIDATE_SUBCOMMANDS } = require('./command-aliases.generated.cjs');
const { formatGsdSlash, resolveRuntime } = require('./runtime-slash.cjs');
const { routeCjsCommandFamily } = require('./cjs-command-router-adapter.cjs');
const { output } = require('./core.cjs');

// ─── SDK bridge (Phase 6) — shared loader via cjs-sdk-bridge.cjs ──────────────
const { tryLoadSdk, getExecuteForCjs } = require('./cjs-sdk-bridge.cjs');

/**
 * Manifest-backed validate subcommand router.
 * Keeps gsd-tools.cjs thin while preserving existing command semantics.
 *
 * Phase 6: validate.consistency, validate.health, validate.agents are
 * dispatched via executeForCjs when the SDK is available. CJS fallback
 * retained when:
 * - GSD_WORKSTREAM is active (workstream-scoped requests fall through to CJS).
 * - SDK is unavailable (build not present).
 *
 * CJS-only subcommands:
 * - context: complex inline logic using classifyContextUtilization and
 *   output formatting that has no direct SDK counterpart. Remains CJS-native.
 *
 * SDK-only (unsupported in CJS router): none.
 */
function routeValidateCommand({ verify, args, cwd, raw, parseNamedArgs, output: outputFn, error }) {
  const activeWorkstream = process.env.GSD_WORKSTREAM;
  const sdkAvailable = !activeWorkstream && tryLoadSdk();

  function sdkHandler(registryCommand, registryArgs, legacyArgs, cjsFallback) {
    if (!sdkAvailable) return cjsFallback;
    return () => {
      const result = getExecuteForCjs()({
