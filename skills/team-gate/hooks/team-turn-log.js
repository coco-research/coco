#!/usr/bin/env node
'use strict';

// team-turn-log.js -- UserPromptSubmit.
//
// Approval provenance: the approval gate needs the human's literal
// words. When a run is active and the raw prompt is an approval,
// appends an "approval" receipt carrying the raw text and its sha256.
// A prompt beginning "override <gate>: <text>" appends an "override"
// receipt carrying the instruction verbatim. This hook never denies and
// never writes to stdout, in either observe or enforce mode; the mode
// switch documented in README.md does not apply to it.
//
// A prompt is an approval only when, after normalising (trim, lower-case,
// collapse internal whitespace to single spaces):
//   (a) it contains no "?" anywhere, so a clarifying question ("approved
//       by whom?") is never mistaken for approval;
//   (b) none of the negation tokens "do not", "don't", "not", "never" or
//       "yet" appears as a whole word anywhere in the prompt. This is a
//       whole-prompt check, not a check on the text before a matched
//       phrase: "approve, but not yet" normalises to "approve" followed
//       by a valid word boundary, which would otherwise record an
//       approval receipt for a sentence that is not one. Fail closed;
//       the human can restate "approve" without the qualifier.
//   (c) either the prompt, with trailing punctuation removed, equals one
//       of the phrases exactly, or the prompt starts with a phrase
//       immediately followed by a word boundary (space, comma, colon,
//       period or exclamation mark, never a letter or digit) -- this is
//       what keeps "proceeding with caution" from matching "proceed",
//       since the character after the shared prefix is the letter "i".

const crypto = require('crypto');
const lib = require('./lib');

const HOOK_NAME = 'team-turn-log';

const APPROVAL_PHRASES = [
  'approve the plan',
  'approve',
  'approved',
  'proceed',
  'go ahead',
  'ship it',
  'lgtm',
  'yes, proceed',
];

const NEGATION_TOKENS = ['do not', "don't", 'not', 'never', 'yet'];
const BOUNDARY_CHARS = new Set([' ', ',', ':', '.', '!']);

// The override form gets the same word-boundary treatment: "override"
// must be followed by real whitespace (never "overridden" or
// "overriding"), and it must match at the start of the prompt with a
// literal colon after the gate name, so "override coverage because" (no
// colon) never matches.
const OVERRIDE_RE = /^override\s+([^:]+):\s*([\s\S]*)$/i;

function normalize(prompt) {
  return prompt.trim().toLowerCase().replace(/\s+/g, ' ');
}

function stripTrailingPunctuation(s) {
  return s.replace(/[.,!:;]+$/, '');
}

function hasNegation(normalized) {
  return NEGATION_TOKENS.some((tok) => new RegExp(`(^|\\s)${tok}(\\s|$)`).test(normalized));
}

function matchesApprovalPhrase(normalized) {
  const stripped = stripTrailingPunctuation(normalized);
  if (APPROVAL_PHRASES.includes(stripped)) {
    return true;
  }
  for (const phrase of APPROVAL_PHRASES) {
    if (!normalized.startsWith(phrase)) continue;
    const nextChar = normalized[phrase.length];
    if (nextChar === undefined || BOUNDARY_CHARS.has(nextChar)) {
      return true;
    }
  }
  return false;
}

function isApproval(rawPrompt) {
  const normalized = normalize(rawPrompt);
  if (normalized.includes('?')) return false;
  if (hasNegation(normalized)) return false;
  return matchesApprovalPhrase(normalized);
}

function main() {
  const raw = lib.readStdin();

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (e) {
    process.exit(0); // malformed JSON: no cwd to resolve a run from
  }

  const cwd = payload.cwd;
  if (!cwd) process.exit(0);

  const found = lib.findRun(cwd);
  if (!found) process.exit(0); // not in a run

  const { repoRoot } = found;

  try {
    const prompt = payload.prompt;
    if (typeof prompt !== 'string' || prompt.length === 0) {
      process.exit(0);
    }

    const trimmed = prompt.trim();

    const overrideMatch = OVERRIDE_RE.exec(trimmed);
    if (overrideMatch) {
      lib.appendReceipt(repoRoot, 'override', {
        gate: overrideMatch[1].trim(),
        instruction: overrideMatch[2].trim(),
        by: 'user',
      }, raw);
      process.exit(0);
    }

    if (isApproval(prompt)) {
      const sha256 = crypto.createHash('sha256').update(prompt, 'utf8').digest('hex');
      lib.appendReceipt(repoRoot, 'approval', { text: prompt, sha256, stage: 'approval' }, raw);
    }

    process.exit(0);
  } catch (err) {
    try {
      lib.blockReceipt(repoRoot, `${HOOK_NAME}: ${err && err.message ? err.message : err}`, { hook: HOOK_NAME }, raw);
    } catch (e2) {
      // Cannot even record the failure; nothing more this hook can do.
    }
    process.exit(0); // this hook never denies, in either mode
  }
}

main();
