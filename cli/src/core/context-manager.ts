import { execSync } from 'node:child_process';
import { basename } from 'node:path';
import type { StateManager } from './state.js';
import type { SkillRegistry } from './skill-registry.js';
import type { TaskQueue } from './task-queue.js';

// --- Types ---

export interface Exchange {
  input: string;
  output: string;
}

export interface ContextManagerDeps {
  state: StateManager;
  skills: SkillRegistry;
  taskQueue?: TaskQueue;
  claudeSummarize?: (prompt: string) => Promise<string>;  // injectable for testing
}

/**
 * ContextManager handles:
 * - Ambient greeting with project context
 * - Session summarization after N exchanges
 * - Context window assembly for token budget
 * - Skill sequence recommendations
 */
export class ContextManager {
  private state: StateManager;
  private skills: SkillRegistry;
  private taskQueue: TaskQueue | null;
  private claudeSummarize: ((prompt: string) => Promise<string>) | null;

  /** In-memory exchange buffer for the current session */
  private exchanges: Exchange[] = [];

  /** Track last recommendation time to rate-limit suggestions */
  private lastRecommendationTime: number = 0;

  /** Minimum interval between recommendations (5 minutes) */
  private static readonly RECOMMENDATION_INTERVAL_MS = 5 * 60 * 1000;

  /** Exchange threshold for triggering summarization */
  private static readonly SUMMARIZE_THRESHOLD = 10;

  /** Max raw exchanges to keep after summarization */
  private static readonly MAX_RAW_EXCHANGES = 5;

  constructor(deps: ContextManagerDeps) {
    this.state = deps.state;
    this.skills = deps.skills;
    this.taskQueue = deps.taskQueue ?? null;
    this.claudeSummarize = deps.claudeSummarize ?? null;
  }

  /**
   * Build the ambient greeting on startup.
   * Format: project (branch). Last session: skill on topic. N tasks queued. Ready.
   * Rules: max 3 lines, max 80 chars per line, "Ready." always last word.
   */
  buildGreeting(): string {
    const cwd = process.cwd();
    const project = basename(cwd) || 'unknown';

    let branch = 'no-git';
    try {
      branch = execSync('git branch --show-current', { cwd, encoding: 'utf-8' }).trim();
    } catch {
      // Not a git repo
    }

    const skillCount = this.skills.size;
    const interrupted = this.state.getInterruptedSessions();
    const queueDepth = this.taskQueue?.depth ?? 0;

    // Last session info
    const recentSessions = this.state.getRecentSessions(1);
    let lastSessionInfo = '';
    if (recentSessions.length > 0) {
      const last = recentSessions[0];
      const argSnippet = last.args.slice(0, 50).trim();
      lastSessionInfo = `Last: ${last.skill}${argSnippet ? ` on ${argSnippet}` : ''}.`;
    }

    // Build lines
    const lines: string[] = [];

    // Line 1: project info
    let line1 = `${project} (${branch}). ${skillCount} skills loaded.`;
    if (line1.length > 80) {
      line1 = `${project} (${branch}). ${skillCount} skills.`;
    }
    lines.push(line1);

    // Line 2: optional context (last session, interrupted, queue)
    const contextParts: string[] = [];
    if (lastSessionInfo) contextParts.push(lastSessionInfo);
    if (interrupted.length > 0) contextParts.push(`${interrupted.length} interrupted session(s).`);
    if (queueDepth > 0) contextParts.push(`${queueDepth} tasks queued.`);

    if (contextParts.length > 0) {
      let line2 = contextParts.join(' ');
      if (line2.length > 80) {
        line2 = line2.slice(0, 77) + '...';
      }
      lines.push(line2);
    }

    // Final line
    lines.push('Ready.');

    return lines.join('\n');
  }

  /**
   * Record an exchange (user input + CoCo response).
   */
  addExchange(input: string, output: string): void {
    this.exchanges.push({ input, output });
  }

  /**
   * Get recent exchanges formatted as a string for Tier 2 context.
   */
  getRecentExchanges(limit: number = 3): string {
    const recent = this.exchanges.slice(-limit);
    if (recent.length === 0) return '(no recent exchanges)';

    return recent
      .map(e => `User: ${e.input}\nCoCo: ${e.output}`)
      .join('\n\n');
  }

  /**
   * Get the number of exchanges in the current buffer.
   */
  get exchangeCount(): number {
    return this.exchanges.length;
  }

  /**
   * Summarize old exchanges when threshold is reached.
   * After summarization, drops old exchanges keeping only the last MAX_RAW_EXCHANGES.
   */
  async summarizeIfNeeded(sessionId: string): Promise<void> {
    if (this.exchanges.length < ContextManager.SUMMARIZE_THRESHOLD) {
      return;
    }

    const exchangesToSummarize = this.exchanges.slice(
      0,
      this.exchanges.length - ContextManager.MAX_RAW_EXCHANGES
    );

    if (exchangesToSummarize.length === 0) return;

    let summary: string;

    if (this.claudeSummarize) {
      const prompt = [
        'Summarize this terminal assistant session into 1-3 factual sentences.',
        'Include: what tasks were completed, which skills were used, and any pending/failed work.',
        'Do not be conversational. Be precise.',
        '',
        'Exchanges:',
        ...exchangesToSummarize.map(e => `User: ${e.input}\nCoCo: ${e.output}`),
      ].join('\n');

      try {
        summary = await this.claudeSummarize(prompt);
      } catch {
        // Local fallback: extract skill names from exchanges
        summary = this.localSummarize(exchangesToSummarize);
      }
    } else {
      summary = this.localSummarize(exchangesToSummarize);
    }

    // Store the summary
    this.state.saveSummary(sessionId, summary, exchangesToSummarize.length);

    // Drop the summarized exchanges, keep only the recent ones
    this.exchanges = this.exchanges.slice(-ContextManager.MAX_RAW_EXCHANGES);
  }

  /**
   * Local fallback summarization (no Claude call).
   * Extracts skill names and first 30 chars of each input.
   */
  private localSummarize(exchanges: Exchange[]): string {
    const inputs = exchanges.map(e => e.input.slice(0, 30)).join('; ');
    return `Session had ${exchanges.length} exchanges: ${inputs}.`;
  }

  /**
   * Build the context window for a new Claude query.
   * Assembles: last 2 summaries + last 5 raw exchanges.
   * Truncates if over token budget (estimated at 4 chars/token).
   */
  buildContextWindow(tokenBudget: number = 1500): string {
    const charBudget = tokenBudget * 4;
    const parts: string[] = [];

    // Add recent summaries (up to 2)
    const summaries = this.state.getRecentSummaries(2);
    if (summaries.length > 0) {
      parts.push('Previous context:');
      for (const s of summaries) {
        parts.push(`  ${s.summary}`);
      }
      parts.push('');
    }

    // Add recent raw exchanges
    const recent = this.exchanges.slice(-ContextManager.MAX_RAW_EXCHANGES);
    if (recent.length > 0) {
      parts.push('Recent exchanges:');
      for (const e of recent) {
        parts.push(`  User: ${e.input}`);
        parts.push(`  CoCo: ${e.output}`);
        parts.push('');
      }
    }

    let result = parts.join('\n');

    // Truncate if over budget
    if (result.length > charBudget) {
      // Drop oldest summaries first, then oldest exchanges
      result = result.slice(-charBudget);
      // Find the first complete line
      const firstNewline = result.indexOf('\n');
      if (firstNewline > 0) {
        result = result.slice(firstNewline + 1);
      }
    }

    return result;
  }

  /**
   * Check if a skill sequence recommendation should be shown.
   * Rate-limited to 1 suggestion per 5 minutes.
   */
  checkRecommendation(justCompletedSkill: string): string | null {
    const now = Date.now();
    if (now - this.lastRecommendationTime < ContextManager.RECOMMENDATION_INTERVAL_MS) {
      return null;
    }

    const top = this.state.getTopSequence(justCompletedSkill);
    if (top && top.count >= 3) {
      this.lastRecommendationTime = now;
      return `You usually run ${top.skill_b} after ${justCompletedSkill} -- want me to queue it?`;
    }

    return null;
  }

  /**
   * Reset the recommendation timer (for testing).
   */
  resetRecommendationTimer(): void {
    this.lastRecommendationTime = 0;
  }
}
