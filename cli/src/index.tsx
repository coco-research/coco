#!/usr/bin/env node
import { render } from 'ink';
import React from 'react';
import { App } from './ui/App.js';
import { Orchestrator } from './core/orchestrator.js';
import { SessionManager } from './core/session-manager.js';
import { TaskQueue } from './core/task-queue.js';
import { StateManager } from './core/state.js';
import { SkillRegistry } from './core/skill-registry.js';
import { IntentClassifier } from './core/intent-classifier.js';
import { LearningStore } from './core/learning-store.js';
import { ContextManager } from './core/context-manager.js';
import { TeamRouter } from './integrations/team-router.js';
import { GsdRouter } from './integrations/gsd-router.js';
import { ProactiveEngine } from './proactive/engine.js';
import { join } from 'node:path';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

async function main() {
  // DB location: ~/.coco/coco.db
  const cocoDir = join(homedir(), '.coco');
  if (!existsSync(cocoDir)) {
    mkdirSync(cocoDir, { recursive: true });
  }
  const dbPath = join(cocoDir, 'coco.db');

  // Load system prompt
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const promptPath = join(__dirname, '..', 'prompts', 'coco-system.md');
  let systemPrompt = 'You are CoCo, a concise terminal assistant.';
  try {
    systemPrompt = readFileSync(promptPath, 'utf-8');
  } catch (err: any) {
    if (err?.code !== 'ENOENT') {
      console.warn('[coco] Failed to load system prompt:', err.message ?? err);
    }
  }

  // Initialize core modules
  const state = new StateManager(dbPath);
  state.initialize();

  const skills = new SkillRegistry();
  await skills.loadAll();

  // Phase 2: SessionManager with configurable concurrency
  const maxConcurrency = parseInt(state.getContext('max_concurrency') || '3', 10);
  const sessionManager = new SessionManager(state, maxConcurrency, systemPrompt);

  // Phase 2: TaskQueue
  const taskQueue = new TaskQueue(state, sessionManager, skills);

  // Phase 4: Intelligence Layer
  state.initializePhase4();

  const learningStore = new LearningStore(state);
  const intentClassifier = new IntentClassifier({ skills, state });
  const contextManager = new ContextManager({ state, skills, taskQueue });
  const teamRouter = new TeamRouter();
  const gsdRouter = new GsdRouter();

  // Phase 5: Proactive Engine (reuses StateManager's DB connection)
  const proactiveEngine = new ProactiveEngine({
    db: state.getDatabase(),
    config: {
      enabled: state.getContext('proactive_enabled') === 'true',
      sensitivity: (state.getContext('proactive_sensitivity') as 'low' | 'medium' | 'high') ?? 'medium',
      watchPaths: [process.cwd()],
      emailEnabled: false,    // opt-in via /proactive email on
      calendarEnabled: false, // opt-in via /proactive calendar on
      maxSuggestionsPerMinute: 3,
      suggestionTtlMs: 30_000,
    },
    getActiveSkills: () => {
      if (sessionManager) {
        return sessionManager.getActive().map(s => s.skill);
      }
      return [];
    },
    getRecentPaths: () => [],
  });

  // Orchestrator uses options-object pattern (backward-compatible with Phase 1)
  const orchestrator = new Orchestrator({
    state, skills, sessionManager, taskQueue, systemPrompt,
    intentClassifier, learningStore, contextManager, teamRouter, gsdRouter,
    proactiveEngine,
  });
  await orchestrator.startup();

  // Start queue processor
  taskQueue.start();

  // Handle Ctrl+C gracefully
  let ctrlCCount = 0;
  process.on('SIGINT', async () => {
    ctrlCCount++;
    if (ctrlCCount >= 2) {
      taskQueue.stop();
      await sessionManager.killAll();
      await orchestrator.shutdown();
      process.exit(0);
    }
  });

  process.on('SIGTERM', async () => {
    taskQueue.stop();
    await sessionManager.killAll();
    await orchestrator.shutdown();
    process.exit(0);
  });

  // Single-command mode: coco "research OAuth"
  const args = process.argv.slice(2);
  if (args.length > 0) {
    const input = args.join(' ');
    orchestrator.on('output', ({ text }) => process.stdout.write(text + '\n'));
    sessionManager.on('sessionOutput', ({ text }) => process.stdout.write(text));

    await orchestrator.handleInput(input);

    // Wait for any spawned session to finish
    const running = () => sessionManager.getAll().some(s => s.status === 'running' || s.status === 'queued');
    if (running()) {
      await new Promise<void>((resolve) => {
        const check = () => {
          if (!running()) { resolve(); return; }
          sessionManager.once('sessionComplete', check);
          sessionManager.once('sessionError', check);
        };
        check();
      });
    }

    // Clean up after all sessions done
    taskQueue.stop();
    await orchestrator.shutdown();
    return;
  }

  // Interactive TUI mode
  const { waitUntilExit } = render(
    <App
      orchestrator={orchestrator}
      sessionManager={sessionManager}
      taskQueue={taskQueue}
      state={state}
      skills={skills}
    />
  );

  await waitUntilExit();
  taskQueue.stop();
  await sessionManager.killAll();
  await orchestrator.shutdown();
}

main().catch((err) => {
  console.error('CoCo failed to start:', err.message);
  process.exit(1);
});
