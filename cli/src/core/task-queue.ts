import { EventEmitter } from 'eventemitter3';
import type { StateManager } from './state.js';
import type { SessionManager } from './session-manager.js';
import type { SkillRegistry, Skill } from './skill-registry.js';

// --- Types ---

export interface QueuedTask {
  id: string;
  skill: string;
  args: string;
  cwd: string;
  priority: number;
  dependsOn: string | null;
  createdAt: number;
}

export interface TaskQueueEvents {
  taskEnqueued: (task: QueuedTask) => void;
  taskDispatched: (data: { taskId: string; sessionId: string }) => void;
  taskRemoved: (data: { taskId: string }) => void;
  queueCleared: (data: { count: number }) => void;
  queueEmpty: () => void;
}

// --- TaskQueue ---

export class TaskQueue extends EventEmitter<TaskQueueEvents> {
  private state: StateManager;
  private sessionManager: SessionManager;
  private skillRegistry: SkillRegistry;
  private pollInterval: ReturnType<typeof setInterval> | null = null;
  private isProcessing: boolean = false;

  constructor(state: StateManager, sessionManager: SessionManager, skillRegistry: SkillRegistry) {
    super();
    this.state = state;
    this.sessionManager = sessionManager;
    this.skillRegistry = skillRegistry;

    // When a session completes, check if any queued tasks are now unblocked
    this.sessionManager.on('sessionComplete', () => {
      this.processNext();
    });
  }

  /**
   * Start polling the queue for dispatchable tasks.
   */
  start(): void {
    this.pollInterval = setInterval(() => this.processNext(), 2000);
    // Process immediately on start
    this.processNext();
  }

  /**
   * Stop the queue processor.
   */
  stop(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  /**
   * Add a task to the queue.
   */
  enqueue(
    skill: string,
    args: string,
    cwd: string,
    priority: number = 0,
    dependsOn?: string
  ): string {
    const id = this.state.enqueueTask(skill, args, cwd, priority, dependsOn);
    const task: QueuedTask = {
      id,
      skill,
      args,
      cwd,
      priority,
      dependsOn: dependsOn || null,
      createdAt: Date.now(),
    };
    this.emit('taskEnqueued', task);

    // Try to dispatch immediately if there's capacity
    this.processNext();

    return id;
  }

  /**
   * Remove a task from the queue by ID.
   */
  remove(taskId: string): boolean {
    const removed = this.state.removeFromQueue(taskId);
    if (removed) {
      this.emit('taskRemoved', { taskId });
    }
    return removed;
  }

  /**
   * Clear all pending tasks.
   */
  clear(): number {
    const count = this.state.clearQueue();
    this.emit('queueCleared', { count });
    return count;
  }

  /**
   * Promote a task to the front of the queue (highest priority).
   */
  promote(taskId: string): void {
    this.state.promoteTask(taskId);
    this.processNext();
  }

  /**
   * Get all pending tasks in priority order.
   */
  getPending(): QueuedTask[] {
    return this.state.getQueuedTasks().map(row => ({
      id: row.id,
      skill: row.skill,
      args: row.args,
      cwd: '',
      priority: row.priority,
      dependsOn: row.depends_on,
      createdAt: row.created_at,
    }));
  }

  /**
   * Get the number of pending tasks.
   */
  get depth(): number {
    return this.state.getQueueDepth();
  }

  /**
   * Try to dispatch queued tasks while there is concurrency capacity.
   * Uses a while loop instead of recursion to avoid re-entrancy issues.
   */
  private async processNext(): Promise<void> {
    if (this.isProcessing) return;
    this.isProcessing = true;

    try {
      while (true) {
        const stats = this.sessionManager.getStats();

        // Only dispatch if under the concurrency limit
        if (stats.running >= stats.max) break;

        const task = this.state.dequeueTask();
        if (!task) {
          if (this.state.getQueueDepth() === 0) {
            this.emit('queueEmpty');
          }
          break;
        }

        // Look up the skill
        const skill = this.skillRegistry.get(task.skill);
        const skillDescriptor = skill || {
          name: task.skill,
          command: `/${task.skill}`,
          description: task.skill,
          isWriteOperation: false,
        };

        const sessionId = await this.sessionManager.spawn(skillDescriptor, task.args, task.cwd);
        this.emit('taskDispatched', { taskId: task.id, sessionId });
      }
    } finally {
      this.isProcessing = false;
    }
  }
}
