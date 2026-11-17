'use strict';

/**
 * gsd2-import — Reverse migration from GSD-2 (.gsd/) to GSD v1 (.planning/)
 *
 * Reads a GSD-2 project directory structure and produces a complete
 * .planning/ artifact tree in GSD v1 format.
 *
 * GSD-2 hierarchy:  Milestone → Slice → Task
 * GSD v1 hierarchy: Milestone (in ROADMAP.md) → Phase → Plan
 *
 * Mapping rules:
 *   - Slices are numbered sequentially across all milestones (01, 02, …)
 *   - Tasks within a slice become plans (01-01, 01-02, …)
 *   - Completed slices ([x] in ROADMAP) → [x] phases in ROADMAP.md
 *   - Tasks with a SUMMARY file → SUMMARY.md written
 *   - Slice RESEARCH.md → phase XX-RESEARCH.md
 */

const fs = require('node:fs');
const path = require('node:path');
const { platformWriteSync } = require('./shell-command-projection.cjs');

// ─── Utilities ──────────────────────────────────────────────────────────────

function readOptional(filePath) {
  try { return fs.readFileSync(filePath, 'utf8'); } catch { return null; }
}

function zeroPad(n, width = 2) {
  return String(n).padStart(width, '0');
}

function slugify(title) {
  return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

// ─── GSD-2 Parser ───────────────────────────────────────────────────────────

/**
 * Find the .gsd/ directory starting from a project root.
 * Returns the absolute path or null if not found.
 */
function findGsd2Root(startPath) {
  if (path.basename(startPath) === '.gsd' && fs.existsSync(startPath)) {
    return startPath;
  }
  const candidate = path.join(startPath, '.gsd');
  if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
    return candidate;
  }
  return null;
}

/**
 * Parse the ## Slices section from a GSD-2 milestone ROADMAP.md.
 * Each slice entry looks like:
 *   - [x] **S01: Title** `risk:medium` `depends:[S00]`
 */
function parseSlicesFromRoadmap(content) {
  const slices = [];
  const sectionMatch = content.match(/## Slices\n([\s\S]*?)(?:\n## |\n# |$)/);
  if (!sectionMatch) return slices;

  for (const line of sectionMatch[1].split('\n')) {
    const m = line.match(/^- \[([x ])\]\s+\*\*(\w+):\s*([^*]+)\*\*/);
    if (!m) continue;
    slices.push({ done: m[1] === 'x', id: m[2].trim(), title: m[3].trim() });
  }
  return slices;
}

/**
 * Parse the milestone title from the first heading in a GSD-2 ROADMAP.md.
 * Format: # M001: Title
 */
function parseMilestoneTitle(content) {
  const m = content.match(/^# \w+:\s*(.+)/m);
  return m ? m[1].trim() : null;
}

/**
 * Parse a task title from a GSD-2 T##-PLAN.md.
 * Format: # T01: Title
 */
function parseTaskTitle(content, fallback) {
  const m = content.match(/^# \w+:\s*(.+)/m);
  return m ? m[1].trim() : fallback;
}

/**
 * Parse the ## Description body from a GSD-2 task plan.
 */
function parseTaskDescription(content) {
  const m = content.match(/## Description\n+([\s\S]+?)(?:\n## |\n# |$)/);
  return m ? m[1].trim() : '';
}

/**
 * Parse ## Must-Haves items from a GSD-2 task plan.
 */
function parseTaskMustHaves(content) {
  const m = content.match(/## Must-Haves\n+([\s\S]+?)(?:\n## |\n# |$)/);
  if (!m) return [];
  return m[1].split('\n')
    .map(l => l.match(/^- \[[ x]\]\s*(.+)/))
    .filter(Boolean)
    .map(match => match[1].trim());
}

/**
 * Read all task plan files from a GSD-2 tasks/ directory.
 */
function readTasksDir(tasksDir) {
  if (!fs.existsSync(tasksDir)) return [];

  return fs.readdirSync(tasksDir)
    .filter(f => f.endsWith('-PLAN.md'))
    .sort()
    .map(tf => {
      const tid = tf.replace('-PLAN.md', '');
      const plan = readOptional(path.join(tasksDir, tf));
      const summary = readOptional(path.join(tasksDir, `${tid}-SUMMARY.md`));
      return {
        id: tid,
        title: plan ? parseTaskTitle(plan, tid) : tid,
        description: plan ? parseTaskDescription(plan) : '',
        mustHaves: plan ? parseTaskMustHaves(plan) : [],
        plan,
        summary,
        done: !!summary,
      };
    });
}

/**
 * Parse a complete GSD-2 .gsd/ directory into a structured representation.
 */
function parseGsd2(gsdDir) {
  const data = {
    projectContent: readOptional(path.join(gsdDir, 'PROJECT.md')),
    requirements: readOptional(path.join(gsdDir, 'REQUIREMENTS.md')),
    milestones: [],
  };

  const milestonesBase = path.join(gsdDir, 'milestones');
  if (!fs.existsSync(milestonesBase)) return data;

  const milestoneIds = fs.readdirSync(milestonesBase)
    .filter(d => fs.statSync(path.join(milestonesBase, d)).isDirectory())
    .sort();
