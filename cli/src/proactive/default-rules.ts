/**
 * Phase 5: Default Trigger Rules
 *
 * Pre-configured rules for file, email, and calendar events.
 */

import type { TriggerRule } from './types.js';

// --- File Rules ---

export const FILE_RULES: TriggerRule[] = [
  {
    id: 'file:test-added',
    source: 'file',
    condition: (e) => e.type === 'add' && /\.(test|spec)\.(ts|tsx|js|jsx)$/.test(e.path ?? ''),
    actionTemplate: 'New test file added: {filename}. Run tests?',
    skillRoute: 'team-test',
    baseConfidence: 0.80,
    cooldownMs: 5 * 60 * 1000,
  },
  {
    id: 'file:test-changed',
    source: 'file',
    condition: (e) => e.type === 'change' && /\.(test|spec)\.(ts|tsx|js|jsx)$/.test(e.path ?? ''),
    actionTemplate: 'Tests updated: {filename}. Re-run?',
    skillRoute: 'team-test',
    baseConfidence: 0.70,
    cooldownMs: 5 * 60 * 1000,
  },
  {
    id: 'file:batch-change',
    source: 'file',
    condition: (e) => e.type === 'batch-change' && ((e.metadata?.batchSize as number) ?? 0) > 5,
    actionTemplate: 'Bulk changes detected ({detail}). Run review?',
    skillRoute: 'team-review',
    baseConfidence: 0.75,
    cooldownMs: 10 * 60 * 1000,
  },
  {
    id: 'file:package-json-changed',
    source: 'file',
    condition: (e) => e.type === 'change' && (e.path ?? '').endsWith('package.json'),
    actionTemplate: 'Dependencies changed. Run install?',
    skillRoute: 'direct',
    baseConfidence: 0.85,
    cooldownMs: 5 * 60 * 1000,
  },
  {
    id: 'file:claude-config-changed',
    source: 'file',
    condition: (e) => {
      const path = e.path ?? '';
      return e.type === 'change' && (
        path.endsWith('CLAUDE.md') ||
        path.endsWith('CLAUDE.local.md') ||
        path.includes('.claude/')
      );
    },
    actionTemplate: 'Config updated: {filename}. Reload skills?',
    skillRoute: 'direct',
    baseConfidence: 0.90,
    cooldownMs: 5 * 60 * 1000,
  },
  {
    id: 'file:planning-doc-added',
    source: 'file',
    condition: (e) => e.type === 'add' && (e.path ?? '').includes('.planning/') && (e.path ?? '').endsWith('.md'),
    actionTemplate: 'New planning doc: {filename}. Load GSD context?',
    skillRoute: 'gsd-plan',
    baseConfidence: 0.80,
    cooldownMs: 10 * 60 * 1000,
  },
  {
    id: 'file:docker-changed',
    source: 'file',
    condition: (e) => {
      const fname = (e.path ?? '').split('/').pop() ?? '';
      return e.type === 'change' && (fname === 'Dockerfile' || fname === 'docker-compose.yml' || fname === 'docker-compose.yaml');
    },
    actionTemplate: 'Container config changed: {filename}. Rebuild?',
    skillRoute: 'direct',
    baseConfidence: 0.75,
    cooldownMs: 10 * 60 * 1000,
  },
];

// --- Email Rules ---

export const EMAIL_RULES: TriggerRule[] = [
  {
    id: 'email:hxstore-new-content',
    source: 'email',
    condition: (e) => e.type === 'hxstore-new-content',
    actionTemplate: 'New email detected. {detail} Summarize?',
    skillRoute: 'direct',
    baseConfidence: 0.70,
    cooldownMs: 30 * 60 * 1000,
  },
  {
    id: 'email:attachment-document',
    source: 'email',
    condition: (e) => e.type === 'new-attachment' && e.metadata?.kind === 'document',
    actionTemplate: 'New attachment: {filename}. Want me to read it?',
    skillRoute: 'direct',
    baseConfidence: 0.80,
    cooldownMs: 5 * 60 * 1000,
  },
  {
    id: 'email:attachment-image',
    source: 'email',
    condition: (e) => e.type === 'new-attachment' && e.metadata?.kind === 'image',
    actionTemplate: 'New screenshot received: {filename}. Analyze?',
    skillRoute: 'direct',
    baseConfidence: 0.65,
    cooldownMs: 5 * 60 * 1000,
  },
  {
    id: 'email:manual-drop',
    source: 'email',
    condition: (e) => e.type === 'manual-drop',
    actionTemplate: 'File dropped: {filename}. Summarize and extract action items?',
    skillRoute: 'direct',
    baseConfidence: 0.90,
    cooldownMs: 1 * 60 * 1000,
  },
];

// --- Calendar Rules ---

export const CALENDAR_RULES: TriggerRule[] = [
  {
    id: 'calendar:standup-15min',
    source: 'calendar',
    condition: (e) => e.type === 'meeting-standup' && (e.metadata?.alertThreshold as number) === 15,
    actionTemplate: '{detail}. Summarize today\'s commits for your update?',
    skillRoute: 'direct',
    baseConfidence: 0.85,
    cooldownMs: 30 * 60 * 1000,
  },
  {
    id: 'calendar:review-15min',
    source: 'calendar',
    condition: (e) => e.type === 'meeting-review' && (e.metadata?.alertThreshold as number) === 15,
    actionTemplate: '{detail}. Run a quick review?',
    skillRoute: 'team-review',
    baseConfidence: 0.75,
    cooldownMs: 30 * 60 * 1000,
  },
  {
    id: 'calendar:generic-15min',
    source: 'calendar',
    condition: (e) => e.type === 'meeting-generic' && (e.metadata?.alertThreshold as number) === 15,
    actionTemplate: 'Meeting "{detail}".',
    skillRoute: 'direct',
    baseConfidence: 0.50,
    cooldownMs: 30 * 60 * 1000,
  },
  {
    id: 'calendar:any-5min',
    source: 'calendar',
    condition: (e) => (e.metadata?.alertThreshold as number) === 5,
    actionTemplate: '{detail}.',
    skillRoute: 'direct',
    baseConfidence: 0.40,
    cooldownMs: 30 * 60 * 1000,
  },
];

/** All default rules combined. */
export const ALL_DEFAULT_RULES: TriggerRule[] = [
  ...FILE_RULES,
  ...EMAIL_RULES,
  ...CALENDAR_RULES,
];
