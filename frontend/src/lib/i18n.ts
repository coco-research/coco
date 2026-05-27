/**
 * Minimal i18n scaffold — English-only today, structure ready for translations.
 *
 * Usage: `t('settings.title', 'Settings')` — fallback is the source of truth
 * until translations exist. Future work plugs a real catalog into `catalogs`.
 *
 * Phase 11 P9 — Polish.
 */

export type Locale = 'en' | 'es' | 'fr' | 'de' | 'ja' | 'zh';

const STORAGE_KEY = 'coco:locale';
const DEFAULT_LOCALE: Locale = 'en';

/** All locales the UI advertises in the picker. Only `en` ships strings today. */
export const SUPPORTED_LOCALES: { code: Locale; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Espanol (coming soon)' },
  { code: 'fr', label: 'Francais (coming soon)' },
  { code: 'de', label: 'Deutsch (coming soon)' },
  { code: 'ja', label: 'Nihongo (coming soon)' },
  { code: 'zh', label: 'Zhongwen (coming soon)' },
];

// Translation catalogs. Add real string maps here as locales ship.
const catalogs: Partial<Record<Locale, Record<string, string>>> = {
  en: {},
};

function isLocale(value: unknown): value is Locale {
  return SUPPORTED_LOCALES.some((l) => l.code === value);
}

export function getLocale(): Locale {
  if (typeof window === 'undefined') return DEFAULT_LOCALE;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return isLocale(raw) ? raw : DEFAULT_LOCALE;
  } catch {
    return DEFAULT_LOCALE;
  }
}

export function setLocale(locale: Locale): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    /* ignore */
  }
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale;
  }
  listeners.forEach((fn) => fn(locale));
}

/**
 * Translate a key. Returns the catalog entry if present, otherwise the
 * fallback. Today every call resolves to its fallback — the catalogs are
 * intentionally empty until translation files are commissioned.
 */
export function t(key: string, fallback: string): string {
  const locale = getLocale();
  const cat = catalogs[locale];
  if (cat && Object.prototype.hasOwnProperty.call(cat, key)) {
    return cat[key];
  }
  return fallback;
}

type Listener = (locale: Locale) => void;
const listeners = new Set<Listener>();

export function subscribeLocale(fn: Listener): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

/** Hydrate <html lang> from storage on boot. */
export function initLocale(): Locale {
  const locale = getLocale();
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale;
  }
  return locale;
}
