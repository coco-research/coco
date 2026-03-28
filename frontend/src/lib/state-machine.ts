/**
 * Issue Lifecycle State Machine
 *
 * Defines valid states and transitions for todos and tasks.
 * Used by both list/detail views and the board (kanban) view.
 */

// ---- State definitions ----

export const TODO_STATES = ['backlog', 'todo', 'in_progress', 'done', 'archived'] as const;
export type TodoState = (typeof TODO_STATES)[number];

export const TASK_STATES = ['backlog', 'todo', 'in_progress', 'in_review', 'done', 'archived'] as const;
export type TaskState = (typeof TASK_STATES)[number];

// ---- Transition maps ----

export const TODO_TRANSITIONS: Record<TodoState, TodoState[]> = {
  backlog: ['todo', 'archived'],
  todo: ['in_progress', 'backlog', 'archived'],
  in_progress: ['done', 'todo'],
  done: ['archived', 'in_progress'],
  archived: ['backlog'],
};

export const TASK_TRANSITIONS: Record<TaskState, TaskState[]> = {
  backlog: ['todo', 'archived'],
  todo: ['in_progress', 'backlog', 'archived'],
  in_progress: ['in_review', 'done', 'todo'],
  in_review: ['done', 'in_progress'],
  done: ['archived', 'in_progress'],
  archived: ['backlog'],
};

// ---- Display helpers ----

export const STATE_LABELS: Record<string, string> = {
  backlog: 'Backlog',
  todo: 'Todo',
  in_progress: 'In Progress',
  in_review: 'In Review',
  done: 'Done',
  archived: 'Archived',
};

export const STATE_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  backlog: {
    bg: 'bg-zinc-100 dark:bg-zinc-800',
    text: 'text-zinc-600 dark:text-zinc-400',
    dot: 'bg-zinc-400',
  },
  todo: {
    bg: 'bg-blue-100 dark:bg-blue-900/40',
    text: 'text-blue-700 dark:text-blue-300',
    dot: 'bg-blue-500',
  },
  in_progress: {
    bg: 'bg-amber-100 dark:bg-amber-900/40',
    text: 'text-amber-700 dark:text-amber-300',
    dot: 'bg-amber-500',
  },
  in_review: {
    bg: 'bg-purple-100 dark:bg-purple-900/40',
    text: 'text-purple-700 dark:text-purple-300',
    dot: 'bg-purple-500',
  },
  done: {
    bg: 'bg-green-100 dark:bg-green-900/40',
    text: 'text-green-700 dark:text-green-300',
    dot: 'bg-green-500',
  },
  archived: {
    bg: 'bg-zinc-50 dark:bg-zinc-900',
    text: 'text-zinc-400 dark:text-zinc-600',
    dot: 'bg-zinc-300 dark:bg-zinc-700',
  },
};

/** Combined bg+text class for pills/badges */
export function statePillClass(state: string): string {
  const c = STATE_COLORS[state];
  if (!c) return 'bg-accent/50 text-muted-foreground';
  return `${c.bg} ${c.text}`;
}

/** Friendly transition button labels */
export const TRANSITION_LABELS: Record<string, string> = {
  backlog: 'Move to Backlog',
  todo: 'Move to Todo',
  in_progress: 'Start',
  in_review: 'Send to Review',
  done: 'Mark Done',
  archived: 'Archive',
};

/** Short labels for compact button groups */
export const TRANSITION_SHORT_LABELS: Record<string, string> = {
  backlog: 'Backlog',
  todo: 'Todo',
  in_progress: 'Start',
  in_review: 'Review',
  done: 'Done',
  archived: 'Archive',
};
