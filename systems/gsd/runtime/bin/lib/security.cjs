/**
 * Security — Input validation, path traversal prevention, and prompt injection guards
 *
 * This module centralizes security checks for GSD tooling. Because GSD generates
 * markdown files that become LLM system prompts (agent instructions, workflow state,
 * phase plans), any user-controlled text that flows into these files is a potential
 * indirect prompt injection vector.
 *
 * Threat model:
 *   1. Path traversal: user-supplied file paths escape the project directory
 *   2. Prompt injection: malicious text in arguments/PRDs embeds LLM instructions
 *   3. Shell metacharacter injection: user text interpreted by shell
 *   4. JSON injection: malformed JSON crashes or corrupts state
 *   5. Regex DoS: crafted input causes catastrophic backtracking
 */
'use strict';

const fs = require('fs');
const path = require('path');

// ─── Path Traversal Prevention ──────────────────────────────────────────────

/**
 * Validate that a file path resolves within an allowed base directory.
 * Prevents path traversal attacks via ../ sequences, symlinks, or absolute paths.
 *
 * @param {string} filePath - The user-supplied file path
 * @param {string} baseDir - The allowed base directory (e.g., project root)
 * @param {object} [opts] - Options
 * @param {boolean} [opts.allowAbsolute=false] - Allow absolute paths (still must be within baseDir)
 * @returns {{ safe: boolean, resolved: string, error?: string }}
 */
function validatePath(filePath, baseDir, opts = {}) {
  if (!filePath || typeof filePath !== 'string') {
    return { safe: false, resolved: '', error: 'Empty or invalid file path' };
  }

  if (!baseDir || typeof baseDir !== 'string') {
    return { safe: false, resolved: '', error: 'Empty or invalid base directory' };
  }

  // Reject null bytes (can bypass path checks in some environments)
  if (filePath.includes('\0')) {
    return { safe: false, resolved: '', error: 'Path contains null bytes' };
  }

  // Resolve symlinks in base directory to handle macOS /var -> /private/var
  // and similar platform-specific symlink chains
  let resolvedBase;
  try {
    resolvedBase = fs.realpathSync(path.resolve(baseDir));
  } catch {
    resolvedBase = path.resolve(baseDir);
  }

  let resolvedPath;

  if (path.isAbsolute(filePath)) {
    if (!opts.allowAbsolute) {
      return { safe: false, resolved: '', error: 'Absolute paths not allowed' };
    }
    resolvedPath = path.resolve(filePath);
  } else {
    resolvedPath = path.resolve(baseDir, filePath);
  }

  // Resolve symlinks in the target path too
  try {
    resolvedPath = fs.realpathSync(resolvedPath);
  } catch {
    // File may not exist yet (e.g., about to be created) — use logical resolution
    // but still resolve the parent directory if it exists
    const parentDir = path.dirname(resolvedPath);
    try {
      const realParent = fs.realpathSync(parentDir);
      resolvedPath = path.join(realParent, path.basename(resolvedPath));
    } catch {
      // Parent doesn't exist either — keep the resolved path as-is
    }
  }

  // Normalize both paths and check containment
  const normalizedBase = resolvedBase + path.sep;
  const normalizedPath = resolvedPath + path.sep;

  // The resolved path must start with the base directory
  // (or be exactly the base directory)
  if (resolvedPath !== resolvedBase && !normalizedPath.startsWith(normalizedBase)) {
    return {
      safe: false,
      resolved: resolvedPath,
      error: `Path escapes allowed directory: ${resolvedPath} is outside ${resolvedBase}`,
    };
  }

  return { safe: true, resolved: resolvedPath };
}

/**
 * Validate a file path and throw on traversal attempt.
 * Convenience wrapper around validatePath for use in CLI commands.
 */
function requireSafePath(filePath, baseDir, label, opts = {}) {
  const result = validatePath(filePath, baseDir, opts);
  if (!result.safe) {
    throw new Error(`${label || 'Path'} validation failed: ${result.error}`);
  }
  return result.resolved;
}

// ─── Prompt Injection Detection ─────────────────────────────────────────────

/**
 * Patterns that indicate prompt injection attempts in user-supplied text.
 * These patterns catch common indirect prompt injection techniques where
 * an attacker embeds LLM instructions in text that will be read by an agent.
 *
 * Note: This is defense-in-depth — not a complete solution. The primary defense
 * is proper input/output boundaries in agent prompts.
 */
const INJECTION_PATTERNS = [
  // Direct instruction override attempts
  /ignore\s+(all\s+)?previous\s+instructions/i,
  /ignore\s+(all\s+)?above\s+instructions/i,
  /disregard\s+(all\s+)?previous/i,
  /forget\s+(all\s+)?(your\s+)?instructions/i,
  /override\s+(system|previous)\s+(prompt|instructions)/i,

  // Role/identity manipulation
  /you\s+are\s+now\s+(?:a|an|the)\s+/i,
  /act\s+as\s+(?:a|an|the)\s+(?!plan|phase|wave)/i,  // allow "act as a plan"
  /pretend\s+(?:you(?:'re| are)\s+|to\s+be\s+)/i,
  /from\s+now\s+on,?\s+you\s+(?:are|will|should|must)/i,

  // System prompt extraction
  /(?:print|output|reveal|show|display|repeat)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions)/i,
  /what\s+(?:are|is)\s+your\s+(?:system\s+)?(?:prompt|instructions)/i,

  // Hidden instruction markers (XML/HTML tags that mimic system messages)
  // Note: <instructions> is excluded — GSD uses it as legitimate prompt structure
  // Requires > to close the tag (not just whitespace) to avoid matching generic types like Promise<User | null>
  /<\/?(?:system|assistant|human)>/i,
  /\[SYSTEM\]/i,
  /\[\/?(INST)\]/i,
  /<<\s*SYS\s*>>/i,

  // Exfiltration attempts
  /(?:send|post|fetch|curl|wget)\s+(?:to|from)\s+https?:\/\//i,
  /(?:base64|btoa|encode)\s+(?:and\s+)?(?:send|exfiltrate|output)/i,

  // Tool manipulation
  /(?:run|execute|call|invoke)\s+(?:the\s+)?(?:bash|shell|exec|spawn)\s+(?:tool|command)/i,
];

/**
 * Layer 2: Encoding-obfuscation patterns with custom finding messages.
 * Each entry: { pattern: RegExp, message: string }
 */
const OBFUSCATION_PATTERN_ENTRIES = [
  {
    pattern: /\b(\w\s){4,}\w\b/,
    message: 'Character-spacing obfuscation pattern detected (e.g. "i g n o r e")',
  },
  {
    pattern: /<\/?(system|human|assistant|user)\s*>/i,
    message: 'Delimiter injection pattern: <system>/<human>/<assistant>/<user> tag detected',
  },
  {
    pattern: /0x[0-9a-fA-F]{16,}/,
    message: 'Long hex sequence detected — possible encoded payload',
  },
];

/**
 * Scan text for potential prompt injection patterns.
 * Returns an array of findings (empty = clean).
 *
 * @param {string} text - The text to scan
 * @param {object} [opts] - Options
 * @param {boolean} [opts.strict=false] - Enable stricter matching (more false positives)
 * @returns {{ clean: boolean, findings: string[] }}
 */
function scanForInjection(text, opts = {}) {
  if (!text || typeof text !== 'string') {
    return { clean: true, findings: [] };
  }

  const findings = [];

  for (const pattern of INJECTION_PATTERNS) {
    if (pattern.test(text)) {
      findings.push(`Matched injection pattern: ${pattern.source}`);
    }
  }

  // Layer 2: encoding-obfuscation patterns with custom messages
  for (const entry of OBFUSCATION_PATTERN_ENTRIES) {
    if (entry.pattern.test(text)) {
      findings.push(entry.message);
    }
  }

  if (opts.strict) {
    // Check for suspicious Unicode that could hide instructions
    // (zero-width chars, RTL override, homoglyph attacks)
    if (/[\u200B-\u200F\u2028-\u202F\uFEFF\u00AD]/.test(text)) {
      findings.push('Contains suspicious zero-width or invisible Unicode characters');
    }

    // Layer 1: Unicode tag block U+E0000–U+E007F (2025 supply-chain attack vector)
    // These characters are invisible and can embed hidden instructions
    if (/[\uDB40\uDC00-\uDB40\uDC7F]/u.test(text) || /[\u{E0000}-\u{E007F}]/u.test(text)) {
      findings.push('Contains Unicode tag block characters (U+E0000–E007F) — invisible instruction injection vector');
    }

    // Check for extremely long strings that could be prompt stuffing.
    // Normalize CRLF → LF before measuring so Windows checkouts don't inflate the count.
    const normalizedLength = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').length;
    if (normalizedLength > 50000) {
      findings.push(`Suspicious text length: ${normalizedLength} chars (potential prompt stuffing)`);
    }
  }

  return { clean: findings.length === 0, findings };
}

/**
 * Sanitize text that will be embedded in agent prompts or planning documents.
 * Strips known injection markers while preserving legitimate content.
 *
 * This does NOT alter user intent — it neutralizes control characters and
 * instruction-mimicking patterns that could hijack agent behavior.
 *
 * @param {string} text - Text to sanitize
 * @returns {string} Sanitized text
 */
function sanitizeForPrompt(text) {
  if (!text || typeof text !== 'string') return text;

  let sanitized = text;

  // Strip zero-width characters that could hide instructions
  sanitized = sanitized.replace(/[\u200B-\u200F\u2028-\u202F\uFEFF\u00AD]/g, '');

  // Neutralize XML/HTML tags that mimic system boundaries
  // Replace < > with full-width equivalents to prevent tag interpretation
  // Note: <instructions> is excluded — GSD uses it as legitimate prompt structure
  // Matches system|assistant|human|user with optional whitespace before the closing >
  sanitized = sanitized.replace(/<(\/?)\s*(?:system|assistant|human|user)\s*>/gi,
    (_, slash) => `＜${slash || ''}system-text＞`);

  // Neutralize [SYSTEM] / [INST] / [/INST] markers — both opening and closing variants
  sanitized = sanitized.replace(/\[(\/?)(SYSTEM|INST)\]/gi, (_, slash, tag) => `[${slash}${tag.toUpperCase()}-TEXT]`);

  // Neutralize <<SYS>> and <</SYS>> markers (Llama-style delimiters)
  sanitized = sanitized.replace(/<<\/?\s*SYS\s*>>/gi, '«SYS-TEXT»');

  return sanitized;
}

/**
 * Sanitize text that will be displayed back to the user.
