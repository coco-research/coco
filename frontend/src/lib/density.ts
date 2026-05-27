/**
 * Density modes — controls UI spacing + font scale via a single `data-density`
 * attribute on <body>. CSS variables in index.css read this attribute.
 *
 * Phase 11 P9 — Polish.
 */

export type DensityMode = 'compact' | 'cozy' | 'comfortable';

const STORAGE_KEY = 'coco:density';
const DEFAULT_DENSITY: DensityMode = 'cozy';

export function isDensityMode(value: unknown): value is DensityMode {
  return value === 'compact' || value === 'cozy' || value === 'comfortable';
}

/** Read the persisted density mode, defaulting to "cozy". */
export function getDensity(): DensityMode {
  if (typeof window === 'undefined') return DEFAULT_DENSITY;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return isDensityMode(raw) ? raw : DEFAULT_DENSITY;
  } catch {
    return DEFAULT_DENSITY;
  }
}

/** Apply a density mode to <body> + persist. Safe to call before React mounts. */
export function applyDensity(mode: DensityMode): void {
  if (typeof document === 'undefined') return;
  document.body.setAttribute('data-density', mode);
  try {
    window.localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    /* localStorage unavailable — ignore */
  }
}

/** Hydrate density from storage on app boot. Call once near root. */
export function initDensity(): DensityMode {
  const mode = getDensity();
  applyDensity(mode);
  return mode;
}

// Lightweight subscription model so React components can react to changes.
type Listener = (mode: DensityMode) => void;
const listeners = new Set<Listener>();

export function subscribeDensity(fn: Listener): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

export function setDensity(mode: DensityMode): void {
  applyDensity(mode);
  listeners.forEach((fn) => fn(mode));
}
