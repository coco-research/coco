'use strict';

/**
 * Context-utilization classifier for `gsd-health --context`.
 *
 * Pure function. Callers pass tokensUsed + contextWindow; the
 * classifier returns the percent and one of three states. Recommendation
 * strings are NOT in this module — formatting is the renderer's job
 * (see `validate context` in gsd-tools.cjs). That separation lets the
 * copy change without touching this module's tests.
 *
 * Thresholds:
 *   < 60%   healthy   no action
