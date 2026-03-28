import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function timeAgo(date: string | Date): string {
  const now = Date.now();
  // SQLite datetime('now') returns "YYYY-MM-DD HH:MM:SS" (UTC, no T/Z).
  // Append 'Z' so JS treats it as UTC instead of local time.
  let normalized = date;
  if (typeof date === 'string' && /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(date)) {
    normalized = date.replace(' ', 'T') + 'Z';
  }
  const then = new Date(normalized).getTime();
  if (isNaN(then)) return '';
  const diff = Math.floor((now - then) / 1000);
  if (diff < 0) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function formatCost(usd: number): string {
  return `$${usd.toFixed(2)}`;
}
