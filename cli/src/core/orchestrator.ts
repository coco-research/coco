import { EventEmitter } from 'eventemitter3';
import { execFile, execSync } from 'node:child_process';
import type { StateManager, SessionRow } from './state.js';
import type { SkillRegistry, Skill } from './skill-registry.js';
import type { SessionManager } from './session-manager.js';
import type { TaskQueue } from './task-queue.js';
import { notifySessionComplete, notifyQueueDrained } from './notifier.js';
import { VoiceManager } from '../voice/voice-manager.js';
import { IntentClassifier, META_COMMANDS, TEAM_SKILL_TRIGGERS } from './intent-classifier.js';
import type { ClassifiedIntent } from './intent-classifier.js';
import { LearningStore } from './learning-store.js';
import { ContextManager } from './context-manager.js';
import { TeamRouter } from '../integrations/team-router.js';
import { GsdRouter } from '../integrations/gsd-router.js';
import type { ProactiveEngine } from '../proactive/engine.js';

// Re-export ClassifiedIntent for backward compatibility
export type { ClassifiedIntent } from './intent-classifier.js';

export interface OrchestratorEvents {
  output: (data: { sessionId: string | null; text: string }) => void;
  status: (data: { message: string }) => void;
  sessionStart: (data: { sessionId: string; skill: string }) => void;
  sessionEnd: (data: { sessionId: string; skill: string; success: boolean }) => void;
  recovery: (data: { interrupted: SessionRow[] }) => void;
  error: (data: { message: string; error?: Error }) => void;
  // Phase 3: Voice events
  voice_input: (data: { text: string }) => void;
  system_message: (data: { text: string }) => void;
  session_complete: (data: { summary: string }) => void;
  // Phase 5: Proactive events
  proactive_suggestion: (data: { text: string; skillRoute: string }) => void;
  proactive_warning: (data: { message: string }) => void;
}

// --- Cross-phase extensible deps (CRITICAL: options-object pattern) ---

export interface OrchestratorDeps {
  state: StateManager;
  skills: SkillRegistry;
  sessionManager?: SessionManager;
  taskQueue?: TaskQueue;
  voiceManager?: unknown;      // Phase 3+
  systemPrompt?: string;
  // Phase 4: Intelligence Layer (optional — backward compatible)
  intentClassifier?: IntentClassifier;
  learningStore?: LearningStore;
  contextManager?: ContextManager;
  teamRouter?: TeamRouter;
  gsdRouter?: GsdRouter;
  proactiveEngine?: ProactiveEngine;  // Phase 5
}

// --- Orchestrator ---

export class Orchestrator extends EventEmitter<OrchestratorEvents> {
  private state: StateManager;
  private skills: SkillRegistry;
  private sessionManager: SessionManager | null;
  private taskQueue: TaskQueue | null;
  private voiceManager: VoiceManager;
  private systemPrompt: string;
  private isRunning: boolean = false;

  // Phase 4: Intelligence Layer
  private intentClassifier: IntentClassifier | null;
  private learningStore: LearningStore | null;
  private contextManager: ContextManager | null;
  private teamRouter: TeamRouter | null;
  private gsdRouter: GsdRouter | null;
  private proactiveEngine: ProactiveEngine | null;
  private previousSkill: string | null = null;
  private lastIntentLogId: number | null = null;

  constructor(deps: OrchestratorDeps) {
    super();
    this.state = deps.state;
    this.skills = deps.skills;
    this.sessionManager = deps.sessionManager ?? null;
    this.taskQueue = deps.taskQueue ?? null;

    // Phase 4 deps (all optional for backward compatibility)
    this.intentClassifier = deps.intentClassifier ?? null;
    this.learningStore = deps.learningStore ?? null;
    this.contextManager = deps.contextManager ?? null;
    this.teamRouter = deps.teamRouter ?? null;
    this.gsdRouter = deps.gsdRouter ?? null;
    this.proactiveEngine = deps.proactiveEngine ?? null;

    // Use system prompt from deps (loaded once in index.tsx)
    this.systemPrompt = deps.systemPrompt
      ?? 'You are CoCo, a concise terminal assistant. Route requests to the appropriate skill.';

    // Wire up notifications (only when Phase 2 modules are provided)
    if (this.sessionManager) {
      const sm = this.sessionManager;
      sm.on('sessionComplete', ({ sessionId, success, summary }) => {
        notifySessionComplete(
          sm.get(sessionId)?.skill || 'unknown',
          success,
          summary
        );
      });
    }

    if (this.taskQueue && this.sessionManager) {
      const sm = this.sessionManager;
      this.taskQueue.on('queueEmpty', () => {
        const stats = sm.getStats();
        if (stats.running === 0) {
          notifyQueueDrained(stats.completed);
        }
      });
    }

    // Phase 3: Initialize voice manager
    const voiceConfig = {
      pttKey: this.state.getContext('push_to_talk_key') ?? 'f5',
      speakerVoice: this.state.getContext('voice_name') ?? 'Samantha',
      speakerRate: parseInt(this.state.getContext('voice_rate') ?? '200', 10),
      whisperThreads: 4,
    };
    this.voiceManager = (deps.voiceManager as VoiceManager) ?? new VoiceManager(voiceConfig);

    // When voice transcribes text, feed it into the same input pipeline
    this.voiceManager.on('transcription', (text: string) => {
      this.emit('voice_input', { text });
      this.handleInput(text);
    });

    // When a session completes, speak the summary
    this.on('session_complete', (event: { summary: string }) => {
      this.voiceManager.speakResponse(event.summary);
    });
  }

  async startup(): Promise<void> {
    this.isRunning = true;

    // Mark any previously running sessions as interrupted
    const interrupted = this.state.markRunningAsInterrupted();
    if (interrupted > 0) {
      const sessions = this.state.getInterruptedSessions();
      this.emit('recovery', { interrupted: sessions });
    }

    // Prune old events
    this.state.prune(30);

    // Phase 5: Auto-enable proactive mode if it was on in the last session
    if (this.proactiveEngine && this.state.getContext('proactive_enabled') === 'true') {
      this.proactiveEngine.start();
      this.emit('system_message', { text: 'Proactive mode enabled.' });
    }

    // Auto-enable voice if it was on in the last session
    if (this.state.getContext('voice_enabled') === 'true') {
      const msg = this.voiceManager.turnOn();
      this.emit('system_message', { text: msg });
    }
  }

  /** Expose voice manager for App.tsx to wire PTT */
  get voice(): VoiceManager {
    return this.voiceManager;
  }

  async shutdown(): Promise<void> {
    this.isRunning = false;
    // Phase 5: Stop proactive engine
    if (this.proactiveEngine?.isRunning) {
      this.proactiveEngine.stop();
    }
    // Mark running sessions as interrupted for next startup
    this.state.markRunningAsInterrupted();
    this.state.close();
  }

  // --- Main entry point ---

  async handleInput(text: string): Promise<void> {
    const trimmed = text.trim();
    if (!trimmed) return;

    // Log to input history
    this.state.addInputHistory(trimmed);
    this.state.logEvent(null, 'user_input', { text: trimmed });

    // Step 0: Voice meta-commands (before general classification)
    if (trimmed === '/voice on') {
      const msg = this.voiceManager.turnOn();
      this.emit('system_message', { text: msg });
      this.state.setContext('voice_enabled', 'true');
      return;
    }
    if (trimmed === '/voice off') {
      const msg = this.voiceManager.turnOff();
      this.emit('system_message', { text: msg });
      this.state.setContext('voice_enabled', 'false');
      return;
    }
    if (trimmed === '/voice status') {
      const msg = this.voiceManager.status();
      this.emit('system_message', { text: msg });
      return;
    }
    const voiceConfigMatch = trimmed.match(/^\/voice\s+config\s+(\w+)\s+(.+)$/);
    if (voiceConfigMatch) {
      const [, key, value] = voiceConfigMatch;
      const validKeys: Record<string, string> = {
        voice: 'voice_name',
        rate: 'voice_rate',
        key: 'push_to_talk_key',
      };
      if (validKeys[key]) {
        this.state.setContext(validKeys[key], value);
        this.emit('system_message', {
          text: `Voice config updated: ${key} = ${value}. Restart voice to apply.`,
        });
      } else {
        this.emit('system_message', {
          text: `Unknown voice config key: ${key}. Valid keys: voice, rate, key`,
        });
      }
      return;
    }

    // Step 0b: Proactive meta-commands
    if (trimmed.startsWith('/proactive')) {
      this.handleProactiveCommand(trimmed);
      return;
    }

    // Phase 5: Auto-dismiss active suggestion when user types
    if (this.proactiveEngine) {
      this.proactiveEngine.autoDismissSuggestion();
    }

    // Step 1: Classify intent (use Phase 4 IntentClassifier if available)
    let intent: ClassifiedIntent;
    try {
      if (this.intentClassifier) {
        intent = await this.intentClassifier.classify(trimmed);
      } else {
        intent = this.classifyIntent(trimmed);
      }
    } catch (err: any) {
      this.emit('output', { sessionId: null, text: `Classification error: ${err.message}` });
      intent = { skill: null, args: trimmed, confidence: 0, isMetaCommand: false, tier: 'error' as any };
    }

    // Step 2: Handle meta-commands locally
    if (intent.isMetaCommand) {
      // Phase 4: /correct meta-command
      if (intent.metaCommand === 'correct' && intent.metaArgs) {
        this.handleCorrect(intent.metaArgs);
        return;
      }
      this.handleMetaCommand(intent.metaCommand!, intent.metaArgs);
      return;
    }

    // Phase 4: Confidence thresholds for confirmation
    if (intent.skill && intent.confidence >= 0.4 && intent.confidence < 0.7) {
      this.emit('output', {
        sessionId: null,
        text: `Route to ${intent.skill.command}? [Y/n]`,
      });
      // For now, proceed anyway (confirmation UI is a follow-up)
    }

    // Step 3: If a skill was matched, dispatch to claude with that skill context
    if (intent.skill) {
      if (intent.skill.isWriteOperation) {
        this.emit('status', {
          message: `Will route to ${intent.skill.command} (write operation). Proceeding...`,
        });
      } else {
        this.emit('status', {
          message: `Routing to ${intent.skill.command}...`,
        });
      }

      // Phase 4: Use router to extract clean args
      let cleanArgs = intent.args;
      if (intent.skill.category === 'team' && this.teamRouter) {
        const extracted = this.teamRouter.extractParams(intent.skill, intent.args);
        cleanArgs = extracted.args;
      } else if (intent.skill.category === 'gsd' && this.gsdRouter) {
        const extracted = this.gsdRouter.extractParams(intent.skill, intent.args);
        cleanArgs = extracted.args;
      }

      await this.dispatchToSkill(intent.skill, cleanArgs);

      // Phase 4: Record skill sequence and check recommendation
      if (this.learningStore && this.previousSkill) {
        this.learningStore.recordSequence(this.previousSkill, intent.skill.name);
      }
      if (this.contextManager && intent.skill) {
        const recommendation = this.contextManager.checkRecommendation(intent.skill.name);
        if (recommendation) {
          this.emit('output', { sessionId: null, text: recommendation });
        }
      }
      this.previousSkill = intent.skill.name;
      return;
    }

    // Step 4: No skill match -- send directly to Claude as a general query
    this.emit('status', { message: 'Responding...' });
    await this.dispatchDirect(trimmed);
  }

  // --- Phase 4: /correct handler ---

  private handleCorrect(skillName: string): void {
    if (!this.learningStore || !this.lastIntentLogId) {
      this.emit('output', {
        sessionId: null,
        text: 'No recent classification to correct.',
      });
      return;
    }

    // Normalize the skill name: "team-test" or just "test" -> "team-test"
    let resolvedSkill = skillName.trim();
    if (!this.skills.get(resolvedSkill)) {
      // Try prefixing with "team-"
      if (this.skills.get(`team-${resolvedSkill}`)) {
        resolvedSkill = `team-${resolvedSkill}`;
      }
    }

    if (!this.skills.get(resolvedSkill)) {
      this.emit('output', {
        sessionId: null,
        text: `Unknown skill: ${resolvedSkill}. Use /skills to see available skills.`,
      });
      return;
    }

    this.learningStore.recordCorrection(this.lastIntentLogId, resolvedSkill);

    const skill = this.skills.get(resolvedSkill);
    this.emit('output', {
      sessionId: null,
      text: `Got it. Next time I'll route that to ${skill?.command ?? resolvedSkill}.`,
    });
  }

  // --- Intent Classification ---

  classifyIntent(text: string): ClassifiedIntent {
    // Check meta-commands first
    for (const [name, pattern] of Object.entries(META_COMMANDS)) {
      const match = text.match(pattern);
      if (match) {
        return {
          skill: null,
          args: '',
          confidence: 1.0,
          tier: 1,
          isMetaCommand: true,
          metaCommand: name,
          metaArgs: match[2]?.trim(),
        };
      }
    }

    // Check for direct slash commands: "/team research OAuth"
    if (text.startsWith('/')) {
      const skill = this.skills.findByKeyword(text);
      if (skill) {
        const args = text.replace(skill.command, '').trim();
        return { skill, args, confidence: 0.95, tier: 1, isMetaCommand: false };
      }
    }

    // Priority 1: Team skill trigger words
    for (const { pattern, skill: skillName } of TEAM_SKILL_TRIGGERS) {
      if (pattern.test(text)) {
        const teamSkill = this.skills.get(skillName);
        if (teamSkill) {
          return { skill: teamSkill, args: text, confidence: 0.85, tier: 1, isMetaCommand: false };
        }
      }
    }

    // Priority 2: Generic keyword-based matching from registry
    const skill = this.skills.findByKeyword(text);
    if (skill) {
      return { skill, args: text, confidence: 0.7, tier: 1, isMetaCommand: false };
    }

    // No match
    return { skill: null, args: text, confidence: 0, tier: 1, isMetaCommand: false };
  }

  // --- Meta-command handlers ---

  private handleMetaCommand(command: string, args?: string): void {
    switch (command) {
      case 'status': {
        if (this.sessionManager) {
          const stats = this.sessionManager.getStats();
          const active = this.sessionManager.getActive();
          const lines = [
            `Sessions: ${stats.running} running, ${stats.queued} queued, ${stats.completed} done, ${stats.failed} failed`,
            `Concurrency: ${stats.running}/${stats.max}`,
            `Queue depth: ${this.taskQueue?.depth ?? 0}`,
          ];
          if (active.length > 0) {
            lines.push('', 'Active:');
            for (const s of active) {
              const elapsed = Math.floor((Date.now() - s.startedAt) / 1000);
              lines.push(`  [${s.status}] ${s.id.slice(0, 8)} -- ${s.skill} "${s.args.slice(0, 30)}" (${elapsed}s)`);
            }
          }
          this.emit('output', { sessionId: null, text: lines.join('\n') });
        } else {
          // Phase 1 fallback
          const active = this.state.getActiveSessions();
          if (active.length === 0) {
            this.emit('output', { sessionId: null, text: 'No active sessions.' });
          } else {
            const lines = active.map(s =>
              `  [${s.status}] ${s.skill} -- ${s.args.slice(0, 50)}`
            );
            this.emit('output', { sessionId: null, text: `Active sessions:\n${lines.join('\n')}` });
          }
        }
        break;
      }

      case 'history': {
        const recent = this.state.getRecentSessions(20);
        if (recent.length === 0) {
          this.emit('output', { sessionId: null, text: 'No session history.' });
        } else {
          const lines = recent.map(s => {
            const time = new Date(s.created_at).toLocaleTimeString();
            return `  [${time}] ${s.skill} -- ${s.status} -- ${s.args.slice(0, 40)}`;
          });
          this.emit('output', { sessionId: null, text: `Recent sessions:\n${lines.join('\n')}` });
        }
        break;
      }

      case 'help': {
        const skillContext = this.skills.toPromptContext();
        const help = [
          'CoCo -- type naturally or use commands:',
          '',
          'Session commands:',
          '  /status            -- Show all sessions and stats',
          '  /halt              -- Kill all sessions',
          '  /halt <id>         -- Kill a specific session',
          '  /focus <id>        -- Expand a session panel',
          '  /unfocus           -- Collapse all panels',
          '  /detach <id>       -- Detach a running session',
          '  /concurrency <n>   -- Set max parallel sessions (1-7)',
          '',
          'Queue commands:',
          '  /queue             -- Show pending task queue',
          '  /queue clear       -- Clear all queued tasks',
          '  /queue promote <id> -- Move task to front of queue',
          '',
          'Voice commands:',
          '  /voice on          -- Enable voice input/output',
          '  /voice off         -- Disable voice',
          '  /voice status      -- Show voice config and deps',
          '  /voice config <k> <v> -- Set voice/rate/key',
          '',
          'Proactive commands:',
          '  /proactive on|off  -- Enable/disable proactive suggestions',
          '  /proactive sensitivity low|medium|high',
          '  /proactive email on|off',
          '  /proactive calendar on|off',
          '  /proactive stats   -- Show suggestion acceptance rates',
          '  /proactive reset-prefs -- Reset learned preferences',
          '',
          'General:',
          '  /history           -- Show recent sessions',
          '  /skills            -- List all loaded skills',
          '  /help              -- This message',
          '  /quit              -- Exit CoCo',
          '',
          skillContext,
        ].join('\n');
        this.emit('output', { sessionId: null, text: help });
        break;
      }

      case 'skills': {
        const skillContext = this.skills.toPromptContext();
        this.emit('output', { sessionId: null, text: skillContext });
        break;
      }

      case 'halt': {
        if (this.sessionManager) {
          if (args) {
            // Kill specific session
            this.sessionManager.kill(args).then(killed => {
              this.emit('output', {
                sessionId: null,
                text: killed ? `Session ${args!.slice(0, 8)} killed.` : `Session ${args!.slice(0, 8)} not found.`,
              });
            });
          } else {
            // Kill all
            this.sessionManager.killAll().then(count => {
              this.taskQueue?.clear();
              this.emit('output', { sessionId: null, text: `${count} session(s) killed. Queue cleared.` });
            });
          }
        } else {
          this.state.markRunningAsInterrupted();
          this.emit('output', { sessionId: null, text: 'All sessions halted.' });
        }
        break;
      }

      case 'queue': {
        if (!this.taskQueue) {
          this.emit('output', { sessionId: null, text: 'Task queue not available.' });
          break;
        }
        const pending = this.taskQueue.getPending();
        if (pending.length === 0) {
          this.emit('output', { sessionId: null, text: 'Queue is empty.' });
        } else {
          const lines = pending.map((t, i) =>
            `  ${i + 1}. [${t.skill}] ${t.args.slice(0, 40)} (p:${t.priority}${t.dependsOn ? ` after:${t.dependsOn.slice(0, 8)}` : ''})`
          );
          this.emit('output', { sessionId: null, text: `Task queue (${pending.length} pending):\n${lines.join('\n')}` });
        }
        break;
      }

      case 'queue-clear': {
        if (!this.taskQueue) break;
        const count = this.taskQueue.clear();
        this.emit('output', { sessionId: null, text: `Cleared ${count} task(s) from queue.` });
        break;
      }

      case 'queue-promote': {
        if (!this.taskQueue || !args) break;
        this.taskQueue.promote(args);
        this.emit('output', { sessionId: null, text: `Promoted task ${args.slice(0, 8)} to front of queue.` });
        break;
      }

      case 'focus': {
        this.emit('output', { sessionId: null, text: `Focused on session ${args?.slice(0, 8)}` });
        break;
      }

      case 'unfocus': {
        this.emit('output', { sessionId: null, text: 'All panels collapsed.' });
        break;
      }

      case 'detach': {
        if (args && this.sessionManager) {
          const detached = this.sessionManager.detach(args);
          if (detached) {
            this.emit('output', { sessionId: null, text: `Session ${args.slice(0, 8)} detached. It will continue running in the background.` });
          } else {
            this.emit('output', { sessionId: null, text: `Session ${args.slice(0, 8)} not found or not running.` });
          }
        }
        break;
      }

      case 'concurrency': {
        if (args && this.sessionManager) {
          const n = parseInt(args, 10);
          if (n >= 1 && n <= 7) {
            this.sessionManager.setConcurrency(n);
            this.emit('output', { sessionId: null, text: `Max concurrency set to ${n}.` });
          } else {
            this.emit('output', { sessionId: null, text: 'Concurrency must be between 1 and 7.' });
          }
        }
        break;
      }

      case 'quit': {
        this.emit('output', { sessionId: null, text: 'CoCo signing off.' });
        break;
      }
    }
  }

  // --- Dispatch to claude -p with skill context ---

  private async dispatchToSkill(skill: Skill, args: string): Promise<void> {
    this.state.incrementSkillUsage(skill.name);

    // Phase 2: Use SessionManager if available
    if (this.sessionManager && this.taskQueue) {
      const stats = this.sessionManager.getStats();

      if (stats.running >= stats.max) {
        // At capacity -- enqueue instead of blocking
        const taskId = this.taskQueue.enqueue(skill.name, args, process.cwd());
        this.emit('output', {
          sessionId: null,
          text: `Queued: ${skill.command} ${args} (position: ${this.taskQueue.depth})`,
        });
        this.state.logEvent(null, 'task_queued', { skill: skill.name, args, taskId });
        return;
      }

      // Under capacity -- spawn directly
      const sessionId = await this.sessionManager.spawn(skill, args, process.cwd());
      this.emit('sessionStart', { sessionId, skill: skill.name });
      this.state.logEvent(sessionId, 'session_spawned', { skill: skill.name, args });
      return;
    }

    // Phase 1 fallback: direct execFile
    const sessionId = this.state.createSession(skill.name, args, process.cwd());

    this.emit('sessionStart', { sessionId, skill: skill.name });
    this.state.logEvent(sessionId, 'session_spawned', { skill: skill.name, args });

    const prompt = args || `Execute ${skill.command}`;
    const systemPromptWithSkill = [
      this.systemPrompt,
      '',
      `## Current Task`,
      `Route this to: ${skill.command}`,
      `The user wants: ${args}`,
      `Skill description: ${skill.description}`,
    ].join('\n');

    try {
      await this.runClaude(sessionId, prompt, systemPromptWithSkill);
      this.state.updateSessionStatus(sessionId, 'complete');
      this.emit('sessionEnd', { sessionId, skill: skill.name, success: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      this.state.updateSessionStatus(sessionId, 'error', message);
      this.emit('sessionEnd', { sessionId, skill: skill.name, success: false });
      this.emit('error', { message: `Session failed: ${message}` });
    }
  }

  private async dispatchDirect(text: string): Promise<void> {
    // Phase 2: Use SessionManager if available
    if (this.sessionManager) {
      const directSkill = {
        name: 'direct',
        command: '/direct',
        description: 'Direct Claude query',
        isWriteOperation: false,
      };
      const sessionId = await this.sessionManager.spawn(directSkill, text, process.cwd());
      this.emit('sessionStart', { sessionId, skill: 'direct' });
      return;
    }

    // Phase 1 fallback
    const sessionId = this.state.createSession('direct', text, process.cwd());
    this.emit('sessionStart', { sessionId, skill: 'direct' });

    try {
      await this.runClaude(sessionId, text, this.systemPrompt);
      this.state.updateSessionStatus(sessionId, 'complete');
      this.emit('sessionEnd', { sessionId, skill: 'direct', success: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      this.state.updateSessionStatus(sessionId, 'error', message);
      this.emit('sessionEnd', { sessionId, skill: 'direct', success: false });
      this.emit('error', { message: `Session failed: ${message}` });
    }
  }

  // --- claude -p child process (Phase 1 fallback) ---

  private runClaude(sessionId: string, prompt: string, systemPrompt: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const child = execFile(
        'claude',
        ['-p', '--system-prompt', systemPrompt, '--output-format', 'text', prompt],
        {
          maxBuffer: 1024 * 1024 * 10, // 10MB
          cwd: process.cwd(),
          timeout: 300_000, // 5 minute timeout
        },
        (error, _stdout, stderr) => {
          if (error) {
            this.state.appendSessionOutput(sessionId, stderr || error.message);
            reject(error);
            return;
          }
          resolve();
        }
      );

      child.stdout?.on('data', (chunk: Buffer) => {
        const text = chunk.toString();
        this.state.appendSessionOutput(sessionId, text);
        this.emit('output', { sessionId, text });
      });
    });
  }

  // --- Phase 5: Proactive command handler ---

  private handleProactiveCommand(text: string): void {
    if (!this.proactiveEngine) {
      this.emit('system_message', { text: 'Proactive engine not available.' });
      return;
    }

    const parts = text.replace('/proactive', '').trim().split(/\s+/);
    const subCmd = parts[0]?.toLowerCase() ?? '';
    const arg = parts[1]?.toLowerCase() ?? '';

    switch (subCmd) {
      case 'on': {
        this.proactiveEngine.start();
        this.state.setContext('proactive_enabled', 'true');
        this.emit('system_message', { text: 'Proactive mode enabled.' });
        break;
      }
      case 'off': {
        this.proactiveEngine.stop();
        this.state.setContext('proactive_enabled', 'false');
        this.emit('system_message', { text: 'Proactive mode disabled.' });
        break;
      }
      case 'sensitivity': {
        if (arg === 'low' || arg === 'medium' || arg === 'high') {
          this.proactiveEngine.setSensitivity(arg);
          this.state.setContext('proactive_sensitivity', arg);
          this.emit('system_message', { text: `Proactive sensitivity set to ${arg}.` });
        } else {
          this.emit('system_message', { text: 'Usage: /proactive sensitivity low|medium|high' });
        }
        break;
      }
      case 'email': {
        if (arg === 'on') {
          this.proactiveEngine.setEmailEnabled(true);
          this.emit('system_message', { text: 'Email monitoring enabled.' });
        } else if (arg === 'off') {
          this.proactiveEngine.setEmailEnabled(false);
          this.emit('system_message', { text: 'Email monitoring disabled.' });
        } else {
          this.emit('system_message', { text: 'Usage: /proactive email on|off' });
        }
        break;
      }
      case 'calendar': {
        if (arg === 'on') {
          this.proactiveEngine.setCalendarEnabled(true);
          this.emit('system_message', { text: 'Calendar monitoring enabled.' });
        } else if (arg === 'off') {
          this.proactiveEngine.setCalendarEnabled(false);
          this.emit('system_message', { text: 'Calendar monitoring disabled.' });
        } else {
          this.emit('system_message', { text: 'Usage: /proactive calendar on|off' });
        }
        break;
      }
      case 'stats': {
        const stats = this.proactiveEngine.getStats();
        if (stats.length === 0) {
          this.emit('system_message', { text: 'No proactive suggestion data yet.' });
        } else {
          const lines = ['Proactive suggestion stats:', ''];
          for (const s of stats) {
            const rate = s.totalCount > 0 ? `${(s.acceptRate * 100).toFixed(0)}%` : 'N/A';
            lines.push(`  ${s.ruleId}: ${s.acceptCount} accepted, ${s.dismissCount} dismissed, rate=${rate}, adj=${s.confidenceAdj.toFixed(2)}`);
          }
          this.emit('system_message', { text: lines.join('\n') });
        }
        break;
      }
      case 'reset-prefs': {
        this.proactiveEngine.resetPreferences();
        this.emit('system_message', { text: 'Proactive preferences reset.' });
        break;
      }
      default: {
        const status = this.proactiveEngine.isRunning ? 'ON' : 'OFF';
        const config = this.proactiveEngine.getConfig();
        this.emit('system_message', {
          text: [
            `Proactive mode: ${status}`,
            `Sensitivity: ${config.sensitivity}`,
            `Email: ${config.emailEnabled ? 'on' : 'off'}`,
            `Calendar: ${config.calendarEnabled ? 'on' : 'off'}`,
            `Watch paths: ${config.watchPaths.length > 0 ? config.watchPaths.join(', ') : '(none)'}`,
            `Max suggestions/min: ${config.maxSuggestionsPerMinute}`,
            '',
            'Commands: /proactive on|off|sensitivity|email|calendar|stats|reset-prefs',
          ].join('\n'),
        });
        break;
      }
    }
  }

  /** Expose proactive engine for App.tsx to wire suggestion bar */
  get proactive(): ProactiveEngine | null {
    return this.proactiveEngine;
  }

  // --- Getters for UI ---

  getGreeting(): string {
    // Phase 4: Use ContextManager if available
    if (this.contextManager) {
      return this.contextManager.buildGreeting();
    }

    // Fallback: Phase 1 greeting
    const cwd = process.cwd();
    const project = cwd.split('/').pop() || 'unknown';
    let branch = 'no-git';
    try {
      branch = execSync('git branch --show-current', { cwd, encoding: 'utf-8' }).trim();
    } catch {
      // Not a git repo
    }

    const skillCount = this.skills.size;
    const interrupted = this.state.getInterruptedSessions();
    const lines = [
      `${project} (${branch}). ${skillCount} skills loaded.`,
    ];
    if (interrupted.length > 0) {
      lines.push(`${interrupted.length} interrupted session(s) from last run.`);
    }
    lines.push('Ready.');
    return lines.join('\n');
  }
}
