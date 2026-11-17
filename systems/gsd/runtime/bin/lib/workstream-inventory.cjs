'use strict';

/**
 * Workstream Inventory Module
 *
 * Owns discovery and read-only projection of .planning/workstreams/* state.
 * Command handlers should render outputs from this inventory instead of
 * rescanning workstream directories directly.
 *
 * Pure projection logic lives in workstream-inventory-builder.generated.cjs.
 * This module handles I/O orchestration only.
 */

const fs = require('fs');
const path = require('path');
const { toPosixPath, readSubdirectories } = require('./core.cjs');
const scanPhasePlans = require('./plan-scan.cjs');
