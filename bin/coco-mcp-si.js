'use strict';

// Super Intelligence personas, advisory board, and MCP prompts layer (read-only, zero network/model calls).
// ponytail: ceiling = lexical department/persona ranker over 13 JSON registries (~500 personas); upgrade path = precomputed local embedding vectors.

const fs = require('fs');
const path = require('path');

const ATTRIBUTION_RULE = '**<Name> persona**: an AI simulation based on their public record. Not their words, views or endorsement.';
const ATTRIBUTION_FOOTER = 'Personas are AI simulations modeled on the public record of the people named. They are not those people, do not speak for them, and are not endorsed by or affiliated with them. Quoted text is paraphrase unless it links to a primary source. To request removal or correction of a persona, see docs/personas/TAKEDOWN.md. Made with CoCo Super Intelligence.';

const DEPT_SHORT = {
  ai: 'AI', engineering: 'Eng', 'product-design': 'PD', finance: 'Fin', trading: 'Trade',
  'risk-compliance': 'GRC', strategy: 'Strat', 'data-analytics': 'Data', gtm: 'GTM',
  'legal-ip': 'Legal', 'healthcare-life-sciences': 'Health', 'education-edtech': 'Edu', 'climate-energy': 'Climate',
};

const SHORT_TO_DEPT = Object.fromEntries(Object.entries(DEPT_SHORT).map(([k, v]) => [v.toLowerCase(), k]));

const SI_VERBS = {
  Analyse: ['multi-team analysis of a topic', 'Per-persona reads grouped by department; synthesis names strongest cross-team signal and divergence.'],
  Decide: ['cross-team decision matrix (primary verb)', 'Decision matrix: options x personas(department) x verdict, final recommendation, and named dissent.'],
  Review: ['multi-team critique of a document or design', 'Findings per persona classified CRITICAL/MAJOR/MINOR/SUGGESTION, tagged by department, plus ship verdict.'],
  'Re-Analyse': ['re-run a prior analysis with new evidence', 'Diff prior vs updated conclusion across the selected cross-team panel.'],
  'Pre-Mortem': ['failure-mode analysis before launch', 'Top failure modes ranked by persona(department), blind spots, early-warning signals, and mitigations.'],
  'Post-Mortem': ['root-cause analysis of a failure', 'Per-persona 5-Whys tagged by department plus synthesized root cause and remediation.'],
  'Full-Cycle': ['compound Review -> Analyse -> Decide workflow', 'End-to-end multi-stage review, analysis, risk mitigation, and decision matrix with per-step attribution.'],
  Tradeoff: ['side-by-side option comparison across departments', 'Dimensions x options table carrying each department lens, aggregate verdict, and strongest opposing view.'],
  Plan: ['phased execution plan synthesis', 'Phased plan with owner persona(department) per phase and dissenting risk checks from peer departments.'],
  Design: ['architecture and product design pass', 'Component decisions attributed to persona(department) with explicit cost, risk, and UX constraints.'],
  Vote: ['explicit yes/no poll across selected personas', 'Per-persona yes/no vote plus one-sentence rationale, tallied by department and overall.'],
  Debug: ['multi-lens fault diagnosis', 'Ranked root-cause hypotheses tagged by persona(department) and ordered diagnostic checks.'],
  'Stress-Test': ['adversarial cross-team review', 'Adversarial critique per persona(department), severity matrix, and SHIP / HARDEN-THEN-SHIP / DO-NOT-SHIP gate.'],
  Defend: ['steelman argument and counter-objection pass', 'Sharpened thesis, cited supporting stances, strongest cross-team counter-objections, and falsification criteria.'],
  Roast: ['blunt cross-team critique', 'One incisive critique line per persona(department) plus the single highest-leverage fix.'],
};

const PROMPT_KEY_RE = /^[a-z0-9][a-z0-9:._-]{0,127}$/i;

function validPromptKey(raw) {
  if (typeof raw !== 'string') return false;
  const s = raw.trim();
  if (!s || s.length > 128 || s.includes('..') || s.includes('/') || s.includes('\\') || s.includes('\0')) return false;
  return PROMPT_KEY_RE.test(s);
}

function resolveDeptSlug(siIndex, raw) {
  const k = String(raw || '').trim().toLowerCase();
  if (!k) return '';
  if (siIndex.departments.has(k) || k === 'agents') return k;
  return SHORT_TO_DEPT[k] || k;
}

function parsePersonaSections(mdText) {
  const moves = [], stances = [];
  if (!mdText.startsWith('---')) return { moves, stances };
  const end = mdText.indexOf('\n---', 3);
  const lines = (end > 0 ? mdText.slice(3, end) : '').split(/\r?\n/);
  let section = '', cur = null;
  for (const line of lines) {
    const top = /^([a-zA-Z0-9_]+):\s*$/.exec(line);
    if (top) {
      if (cur && cur.stance) stances.push(cur);
      cur = null; section = top[1]; continue;
    }
    if (section === 'signature_moves') {
      const m = /^\s*-\s+(.+)$/.exec(line);
      if (m) moves.push(m[1].trim().replace(/^["']|["']$/g, ''));
    } else if (section === 'public_stances') {
      const st = /^\s*-\s+stance:\s*(.+)$/.exec(line);
      if (st) {
        if (cur && cur.stance) stances.push(cur);
        cur = { stance: st[1].trim().replace(/^["']|["']$/g, ''), url: '' };
      } else if (cur) {
        const u = /^\s*evidence_url:\s*(.+)$/.exec(line);
        if (u) cur.url = u[1].trim().replace(/^["']|["']$/g, '');
      }
    }
  }
  if (cur && cur.stance) stances.push(cur);
  return { moves: moves.slice(0, 4), stances: stances.slice(0, 3) };
}

function buildSiIndex(realCocoDir, helpers) {
  const { isInsideRoot, parseFrontmatter, safeListDir } = helpers;
  const departments = new Map(), personasBySlug = new Map();
  if (!realCocoDir) return { realCocoDir: null, departments, personasBySlug, personas: [] };

  const siRoot = path.join(realCocoDir, 'systems', 'superintelligence');
  let meta = null;
  try { meta = JSON.parse(fs.readFileSync(path.join(siRoot, 'registry.json'), 'utf8')); } catch (_) {}
  const teamsObj = (meta && meta.teams && typeof meta.teams === 'object') ? meta.teams : {};

  for (const deptSlug of Object.keys(teamsObj).sort()) {
    const tInfo = teamsObj[deptSlug];
    if (!tInfo || !tInfo.built) continue;
    const deptDir = path.join(siRoot, deptSlug);
    let reg;
    try { reg = JSON.parse(fs.readFileSync(path.join(deptDir, 'registry.json'), 'utf8')); } catch (_) { continue; }
    const cells = (reg && reg.cells && typeof reg.cells === 'object') ? reg.cells : {};
    const cellText = Object.values(cells).map((c) => `${c.id || ''} ${c.description || ''}`).join(' ');
    const deptPersonas = [], byDeptSlug = new Map();
    const pMap = (reg && reg.personas && typeof reg.personas === 'object') ? reg.personas : {};

    for (const slug of Object.keys(pMap).sort()) {
      const p = pMap[slug];
      if (!p || typeof p !== 'object') continue;
      let realPath = null;
      for (const cand of [
        path.join(deptDir, 'personas', `${slug}.md`),
        (p.file_path && typeof p.file_path === 'string' && !p.file_path.includes('..')) ? path.join(realCocoDir, 'systems', p.file_path) : null,
      ]) {
        if (!cand) continue;
        try {
          const rp = fs.realpathSync(cand);
          if (fs.statSync(rp).isFile() && isInsideRoot(realCocoDir, rp)) { realPath = rp; break; }
        } catch (_) {}
      }
      if (!realPath) continue;
      const record = {
        slug,
        realName: String(p.real_name || slug),
        department: deptSlug,
        teamName: String(reg.team_name || tInfo.name || deptSlug),
        cell: String(p.cell || ''),
        cellDesc: (cells[p.cell] && cells[p.cell].description) ? String(cells[p.cell].description) : '',
        cellRole: String(p.cell_role || 'specialist'),
        archetype: String(p.archetype || ''),
        domains: Array.isArray(p.domains) ? p.domains.map(String) : [],
        conflicts: Array.isArray(p.productive_conflict_with) ? p.productive_conflict_with.map(String) : [],
        voice: String(p.voice_style_excerpt || ''),
        isNative: !p.home_team || p.home_team === reg.team_id,
        realPath,
      };
      deptPersonas.push(record);
      byDeptSlug.set(slug.toLowerCase(), record);
      if (!personasBySlug.has(slug.toLowerCase()) || record.isNative) personasBySlug.set(slug.toLowerCase(), record);
    }

    departments.set(deptSlug, {
      slug: deptSlug,
      short: DEPT_SHORT[deptSlug] || deptSlug,
      name: String(reg.team_name || tInfo.name || deptSlug),
      searchBlob: `${deptSlug} ${reg.team_name || ''} ${reg.description || ''} ${cellText} ${deptPersonas.flatMap((p) => p.domains).join(' ')}`.toLowerCase(),
      personas: deptPersonas,
      bySlug: byDeptSlug,
    });
  }

  for (const dept of departments.values()) {
    for (const r of dept.personas) {
      const native = personasBySlug.get(r.slug.toLowerCase());
      if (native && native !== r) {
        if (r.realName === r.slug) r.realName = native.realName;
        if (!r.archetype) r.archetype = native.archetype;
        if (!r.domains.length) r.domains = native.domains;
        if (!r.conflicts.length) r.conflicts = native.conflicts;
        if (!r.voice) r.voice = native.voice;
      }
    }
    dept.searchBlob += ' ' + dept.personas.flatMap((p) => p.domains).join(' ').toLowerCase();
  }

  for (const ent of safeListDir(path.join(realCocoDir, 'agents'))) {
    if (!ent.isFile() || !ent.name.endsWith('.md')) continue;
    const stem = ent.name.slice(0, -3);
    if (/^[A-Z0-9_-]+$/.test(stem)) continue;
    try {
      const rp = fs.realpathSync(path.join(realCocoDir, 'agents', ent.name));
      if (!isInsideRoot(realCocoDir, rp)) continue;
      const fm = parseFrontmatter(fs.readFileSync(rp, 'utf8'));
      const slug = stem.toLowerCase();
      if (!personasBySlug.has(slug)) {
        personasBySlug.set(slug, {
          slug, realName: String(fm.name || stem), department: 'agents', teamName: 'Coco Specialist Agents',
          cell: 'core-agents', cellDesc: 'Specialist agent role definitions', cellRole: 'specialist',
          archetype: String(fm.description || 'Specialist agent'), domains: [String(fm.domain || 'engineering')],
          conflicts: [], voice: '', isNative: true, realPath: rp,
        });
      }
    } catch (_) {}
  }

  return { realCocoDir, departments, personasBySlug, personas: [...personasBySlug.values()].sort((a, b) => a.slug.localeCompare(b.slug)) };
}

function tokenize(text) {
  return String(text || '').toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length >= 2)
    .map((w) => (w.length > 4 && w.endsWith('ing') ? w.slice(0, -3) : w.length > 3 && w.endsWith('s') ? w.slice(0, -1) : w));
}

function scoreText(blob, rawTerms, stemTerms) {
  let s = 0;
  for (const t of rawTerms) if (t && blob.includes(t)) s += 8;
  for (const st of stemTerms) if (st && blob.includes(st)) s += 5;
  return s;
}

function formatPersonaCard(p, idx, total) {
  let md = '';
  try { md = fs.readFileSync(p.realPath, 'utf8'); } catch (_) {}
  const { moves, stances } = parsePersonaSections(md);
  const lines = [
    idx ? `### Persona Card ${idx}/${total}: ${p.realName} (${p.department} / ${p.cell})` : `### ${p.realName} (${p.department} / ${p.cell})`,
    `- **${p.realName} persona**: an AI simulation based on their public record. Not their words, views or endorsement.`,
    `- **Slug:** \`${p.slug}\` · **Role:** ${p.cellRole} · **Team:** ${p.teamName}`,
    `- **Archetype:** ${p.archetype}`,
  ];
  if (p.domains.length) lines.push(`- **Domains:** ${p.domains.slice(0, 5).join('; ')}`);
  if (moves.length) lines.push(`- **Signature moves:** ${moves.slice(0, 3).join(' | ')}`);
  if (stances.length) lines.push(`- **Documented public stances:** ${stances.slice(0, 2).map((st) => `${st.stance}${st.url ? ` (${st.url})` : ' [paraphrase]'}`).join(' · ')}`);
  if (p.conflicts.length) lines.push(`- **Productive conflict peers:** ${p.conflicts.join(', ')}`);
  return {
    markdown: lines.join('\n'),
    card: {
      slug: p.slug, department: p.department, cell: p.cell, role: p.cellRole, archetype: p.archetype,
      persona_label: `${p.realName} persona: an AI simulation based on their public record. Not their words, views or endorsement.`,
      domains: p.domains.slice(0, 5), signature_moves: moves.slice(0, 3), productive_conflict_with: p.conflicts,
    },
  };
}

function readPersonaResource(siIndex, rawDept, rawSlug, helpers) {
  const { validLookupKey } = helpers;
  if (!validLookupKey(rawDept) || !validLookupKey(rawSlug) || rawDept.includes(':') || rawSlug.includes(':')) {
    return { ok: false, code: -32602, message: 'Refused persona URI: invalid department or persona name.' };
  }
  const deptSlug = resolveDeptSlug(siIndex, rawDept);
  const dept = siIndex.departments.get(deptSlug);
  if (!dept) return { ok: false, code: -32002, message: `Unknown persona department: '${rawDept}'.` };
  const p = dept.bySlug.get(rawSlug.trim().toLowerCase());
  if (!p) return { ok: false, code: -32002, message: `Unknown persona '${rawSlug}' in '${deptSlug}'.` };
  const rendered = formatPersonaCard(p, 0, 0);
  return { ok: true, uri: `coco://persona/${deptSlug}/${p.slug}`, text: `${rendered.markdown}\n\n---\n${ATTRIBUTION_FOOTER}` };
}

function callPersona(siIndex, args, helpers) {
  const { validLookupKey } = helpers;
  const rawName = typeof args.name === 'string' ? args.name.trim() : '';
  const rawQuery = typeof args.query === 'string' ? args.query.trim() : '';
  const rawDeptInput = typeof args.department === 'string' ? args.department.trim() : '';
  const limit = Math.min(20, Math.max(1, parseInt(args.limit, 10) || 5));

  if (rawName && !validLookupKey(rawName) && (rawName.includes('..') || rawName.includes('/') || rawName.includes('\\'))) {
    return { ok: false, message: 'Refused persona lookup: invalid name or path traversal.' };
  }
  let deptFilter = '';
  if (rawDeptInput) {
    if (!validLookupKey(rawDeptInput)) return { ok: false, message: 'Refused persona lookup: invalid department.' };
    deptFilter = resolveDeptSlug(siIndex, rawDeptInput);
    if (!siIndex.departments.has(deptFilter) && deptFilter !== 'agents') {
      return { ok: false, message: `Refused persona lookup: unknown department '${rawDeptInput}'.` };
    }
  }

  if (rawName) {
    const exactKey = rawName.toLowerCase();
    const pool = (deptFilter && siIndex.departments.has(deptFilter)) ? siIndex.departments.get(deptFilter).personas : siIndex.personas;
    const hit = pool.find((p) => (!deptFilter || p.department === deptFilter) && (p.slug === exactKey || p.realName.toLowerCase() === exactKey));
    if (hit) return { ok: true, text: `${formatPersonaCard(hit, 0, 0).markdown}\n\n---\n${ATTRIBUTION_FOOTER}` };
  }

  const q = (rawQuery || rawName).toLowerCase();
  if (!q && !deptFilter) return { ok: false, message: 'Provide `name`, `query`, or `department` to look up personas.' };
  const rawTerms = q.split(/[^a-z0-9._-]+/).filter(Boolean), stemTerms = tokenize(q);
  const pool = (deptFilter && siIndex.departments.has(deptFilter)) ? siIndex.departments.get(deptFilter).personas : siIndex.personas;
  const scored = [];
  for (const p of pool) {
    if (deptFilter && p.department !== deptFilter) continue;
    if (!q) { scored.push({ p, score: 1 }); continue; }
    const blob = `${p.slug} ${p.realName} ${p.department} ${p.cell} ${p.cellDesc} ${p.archetype} ${p.domains.join(' ')} ${p.voice}`.toLowerCase();
    let score = scoreText(blob, rawTerms, stemTerms);
    if (p.slug.includes(q) || p.realName.toLowerCase().includes(q)) score += 25;
    if (score > 0) scored.push({ p, score });
  }
  if (!scored.length) return { ok: false, message: `No matching personas found for '${rawQuery || rawName || rawDeptInput}'.` };
  scored.sort((a, b) => (b.score - a.score) || a.p.slug.localeCompare(b.p.slug));
  const cards = scored.slice(0, limit).map((s, i) => formatPersonaCard(s.p, i + 1, Math.min(limit, scored.length)).markdown);
  return { ok: true, text: `Coco personas (${cards.length}):\n\n${cards.join('\n\n')}\n\n---\n${ATTRIBUTION_FOOTER}` };
}

function inferVerb(question, explicitVerb) {
  if (explicitVerb && SI_VERBS[explicitVerb]) return explicitVerb;
  const q = question.toLowerCase();
  if (/\b(vs|versus|trade-?off|compare)\b/.test(q)) return 'Tradeoff';
  if (/\b(fail|kill|wrong|pre-?mortem)\b/.test(q)) return 'Pre-Mortem';
  if (/\b(stress|attack|holes|adversar)\b/.test(q)) return 'Stress-Test';
  if (/\b(plan|roadmap|sequence)\b/.test(q)) return 'Plan';
  return 'Decide';
}

function callBoard(siIndex, args, helpers) {
  const { validLookupKey } = helpers;
  const question = String(args.question || args.prompt || args.topic || '').trim();
  if (!question) return { ok: false, message: 'Refused board selection: non-empty `question` is required.' };

  let requestedDepts = null;
  let maxDepts = parseInt(args.max_departments || args.dept_count || '', 10) || 3;
  if (typeof args.departments === 'number') maxDepts = args.departments;
  else if (Array.isArray(args.departments) && args.departments.length > 0) requestedDepts = args.departments.map((d) => String(d).trim()).filter(Boolean);
  else if (typeof args.departments === 'string' && args.departments.trim()) {
    if (/^\d+$/.test(args.departments.trim())) maxDepts = parseInt(args.departments.trim(), 10);
    else requestedDepts = args.departments.split(',').map((d) => d.trim()).filter(Boolean);
  }
  maxDepts = Math.min(13, Math.max(1, maxDepts));
  const perDept = Math.min(4, Math.max(1, parseInt(args.per_department || '', 10) || 1));

  const rawTerms = question.toLowerCase().split(/[^a-z0-9._-]+/).filter(Boolean), stemTerms = tokenize(question);
  let chosenDepts = [];
  if (requestedDepts) {
    for (const rawD of requestedDepts) {
      if (!validLookupKey(rawD)) return { ok: false, message: `Refused board selection: invalid department '${rawD}'.` };
      const resolved = resolveDeptSlug(siIndex, rawD);
      if (!siIndex.departments.has(resolved)) return { ok: false, message: `Refused board selection: unknown department '${rawD}'.` };
      if (!chosenDepts.includes(resolved)) chosenDepts.push(resolved);
    }
  } else {
    const deptScores = [];
    for (const [slug, dObj] of siIndex.departments.entries()) {
      let score = scoreText(dObj.searchBlob, rawTerms, stemTerms);
      if (/pric|monetiz|tier|pack|gtm|revenue|arpu|churn/i.test(question)) {
        if (slug === 'gtm') score += 30;
        if (slug === 'strategy') score += 22;
        if (slug === 'finance') score += 20;
        if (slug === 'product-design') score += 16;
      }
      deptScores.push({ slug, score });
    }
    deptScores.sort((a, b) => (b.score - a.score) || a.slug.localeCompare(b.slug));
    chosenDepts = deptScores.slice(0, maxDepts).map((d) => d.slug);
  }

  const totalTarget = args.size ? Math.min(16, Math.max(1, parseInt(args.size, 10) || chosenDepts.length)) : (chosenDepts.length * perDept);
  const picked = [], pickedSlugs = new Set();
  const roleWeight = { 'lead-driver': 6, validator: 4, specialist: 3, swing: 2 };

  while (picked.length < totalTarget) {
    let addedInPass = false;
    for (const deptSlug of chosenDepts) {
      if (picked.length >= totalTarget) break;
      const dept = siIndex.departments.get(deptSlug);
      if (!dept) continue;
      let best = null, bestScore = -1;
      for (const p of dept.personas) {
        if (pickedSlugs.has(p.slug)) continue;
        const pBlob = `${p.slug} ${p.realName} ${p.cell} ${p.cellDesc} ${p.archetype} ${p.domains.join(' ')}`.toLowerCase();
        let sc = scoreText(pBlob, rawTerms, stemTerms) * 2 + (roleWeight[p.cellRole] || 2) + (p.isNative ? 2 : 0);
        if (picked.some((prev) => p.conflicts.includes(prev.slug) || prev.conflicts.includes(p.slug))) sc += 5;
        if (sc > bestScore || (sc === bestScore && best && p.slug < best.slug)) { best = p; bestScore = sc; }
      }
      if (best) { picked.push(best); pickedSlugs.add(best.slug); addedInPass = true; }
    }
    if (!addedInPass) break;
  }

  const verb = inferVerb(question, typeof args.verb === 'string' ? args.verb.trim() : '');
  const renderedCards = picked.map((p, i) => formatPersonaCard(p, i + 1, picked.length));
  const protocolSteps = [
    'Round 1 (Independent Positions): Voice each selected persona independently (1-2 sentence stance grounded in their cited public record + 1 open question routed to a peer slug).',
    'Conflict Routing: Route reactions strictly along `productive_conflict_with` pairs and opposing department lenses rather than generic consensus.',
    'Rounds 2-3 (React & Move): Record explicit stance transitions (`held | sharpened | updated | conceded | hardened`) and what evidence moved each position.',
    `Synthesis (${verb}): Produce ${SI_VERBS[verb][1]} If genuinely divided, report SPLIT with 2-3 falsifiable decision criteria instead of forcing false agreement.`,
  ];

  const md = [
    `# Coco Super Intelligence Board — /SI-${verb}`,
    `- **Question:** ${question}`,
    `- **Departments (${chosenDepts.length}):** ${chosenDepts.join(', ')}`,
    `- **Selected Persona Cards (${renderedCards.length}):** ${picked.map((p) => `${p.slug} (${p.department})`).join(', ')}`,
    '',
    '## Persona Cards',
    renderedCards.map((r) => r.markdown).join('\n\n'),
    '',
    '## Structured Debate Protocol (0 server model calls; run in host session)',
    protocolSteps.map((s, idx) => `${idx + 1}. ${s}`).join('\n'),
    '',
    '## Mandatory Attribution Rule',
    `- ${ATTRIBUTION_RULE}`,
    `- ${ATTRIBUTION_FOOTER}`,
  ].join('\n');

  return {
    ok: true,
    text: md,
    structured: {
      question, verb: `SI-${verb}`, departments: chosenDepts,
      persona_cards: renderedCards.map((r) => r.card),
      debate_protocol: { max_rounds: 4, steps: protocolSteps, attribution_rule: ATTRIBUTION_RULE },
    },
  };
}

function buildPromptIndex(realCocoDir, skillIndex, siIndex, helpers) {
  const { isInsideRoot, parseFrontmatter, safeListDir } = helpers;
  const byName = new Map(), list = [];
  if (!realCocoDir) return { byName, list };
  const deptList = [...siIndex.departments.keys()].join(', ');
  const addPrompt = (entry) => {
    const k = entry.name.toLowerCase();
    if (!byName.has(k)) { byName.set(k, entry); list.push(entry); }
  };

  addPrompt({
    name: 'SI',
    description: 'Super Intelligence front-door dispatcher across all built departments.',
    arguments: [{ name: 'topic', description: 'Decision, design, or question for the advisory board.', required: false }],
    render: (a) => `# /SI — Super Intelligence Front Door\nBuilt departments (${siIndex.departments.size}): ${deptList}.\nCall \`coco_board\` with the user question to fetch grounded persona cards and the structured debate protocol.\nAttribution: ${ATTRIBUTION_RULE}\nFooter: ${ATTRIBUTION_FOOTER}${a.topic ? `\n\nARGUMENTS:\n${a.topic}` : ''}`,
  });

  addPrompt({
    name: 'SI-Orchestrate',
    description: 'Two-stage cross-department Super Intelligence panel selector and debate protocol.',
    arguments: [{ name: 'topic', description: 'Prompt to route across Super Intelligence departments.', required: false }],
    render: (a) => `# /SI-Orchestrate\nDepartments: ${deptList}.\nCall \`coco_board\` to select conflict-balanced persona cards, then run Round 1 stances -> conflict reactions -> synthesis.\nAttribution: ${ATTRIBUTION_RULE}\nFooter: ${ATTRIBUTION_FOOTER}${a.topic ? `\n\nARGUMENTS:\n${a.topic}` : ''}`,
  });

  for (const [verb, [shortDesc, outputShape]] of Object.entries(SI_VERBS)) {
    const name = `SI-${verb}`;
    addPrompt({
      name,
      description: `Super Intelligence ${shortDesc}.`,
      arguments: [{ name: 'topic', description: 'Question or proposal to evaluate.', required: false }],
      render: (a) => `# /${name} — ${shortDesc}\nDepartments: ${deptList}.\n1. Call \`coco_board\` on the topic to load persona cards + debate protocol.\n2. Run Round 1 independent positions -> productive-conflict reactions (\`held | sharpened | updated | conceded | hardened\`).\n3. Output shape: ${outputShape}\nAttribution: ${ATTRIBUTION_RULE}\nFooter: ${ATTRIBUTION_FOOTER}${a.topic ? `\n\nARGUMENTS:\n${a.topic}` : ''}`,
    });
  }

  for (const s of skillIndex.list) {
    if (s.source === 'core' && validPromptKey(s.name)) {
      addPrompt({
        name: s.name,
        description: String(s.description || `Coco ${s.name} skill`).slice(0, 120),
        arguments: [{ name: 'topic', description: 'Task context to apply this skill to.', required: false }],
        realPath: s.realPath,
      });
    }
  }

  for (const [deptSlug, dept] of siIndex.departments.entries()) {
    for (const [verb, [shortDesc, outputShape]] of Object.entries(SI_VERBS)) {
      const name = `SI-${dept.short}-${verb}`;
      addPrompt({
        name,
        description: `${dept.name}: ${shortDesc}.`.slice(0, 120),
        arguments: [{ name: 'topic', description: 'Question or artifact for this department.', required: false }],
        render: (a) => `# /${name} — ${dept.name}\n1. Call \`coco_board\` with \`departments: ["${deptSlug}"]\` and \`size: 4\` on the topic.\n2. Output shape: ${outputShape}\nAttribution: ${ATTRIBUTION_RULE}\nFooter: ${ATTRIBUTION_FOOTER}${a.topic ? `\n\nARGUMENTS:\n${a.topic}` : ''}`,
      });
    }
  }

  for (const nsEnt of safeListDir(path.join(realCocoDir, 'commands'))) {
    if (!nsEnt.isDirectory() || nsEnt.name.startsWith('.')) continue;
    for (const fEnt of safeListDir(path.join(realCocoDir, 'commands', nsEnt.name))) {
      if (!fEnt.isFile() || !fEnt.name.endsWith('.md')) continue;
      const stem = fEnt.name.slice(0, -3);
      if (/^[A-Z0-9_-]+$/.test(stem) || stem.startsWith('_')) continue;
      try {
        const rp = fs.realpathSync(path.join(realCocoDir, 'commands', nsEnt.name, fEnt.name));
        if (!isInsideRoot(realCocoDir, rp)) continue;
        const fm = parseFrontmatter(fs.readFileSync(rp, 'utf8'));
        const name = `${nsEnt.name}:${stem}`;
        if (validPromptKey(name)) {
          addPrompt({
            name, description: String(fm.description || `Coco /${name} command`).slice(0, 120),
            arguments: [{ name: 'topic', description: 'Command arguments.', required: false }], realPath: rp,
          });
        }
      } catch (_) {}
    }
  }

  return { byName, list };
}

function getPrompt(promptIndex, realCocoDir, rawName, rawArgs, helpers) {
  const { isInsideRoot } = helpers;
  if (!validPromptKey(rawName)) return { ok: false, code: -32602, message: 'Refused prompt lookup: invalid name or path traversal.' };
  const entry = promptIndex.byName.get(rawName.trim().toLowerCase());
  if (!entry) return { ok: false, code: -32602, message: `Unknown prompt: '${rawName.trim()}'.` };
  const args = (rawArgs && typeof rawArgs === 'object' && !Array.isArray(rawArgs)) ? rawArgs : {};
  const topic = String(args.topic || args.arguments || args.question || '').trim();
  let body = '';
  if (typeof entry.render === 'function') body = entry.render({ topic });
  else if (entry.realPath && isInsideRoot(realCocoDir, entry.realPath)) {
    try { body = fs.readFileSync(entry.realPath, 'utf8'); } catch (_) { return { ok: false, code: -32602, message: `Unreadable prompt: '${entry.name}'.` }; }
    if (topic) body += `\n\nARGUMENTS:\n${topic}`;
  }
  return { ok: true, entry, text: body };
}

function siTools(readOnlyAnnotations) {
  return [
    {
      name: 'coco_persona',
      description: 'Look up or search Coco Super Intelligence personas and specialist agents (read-only, zero network calls).',
      annotations: readOnlyAnnotations,
      inputSchema: {
        type: 'object',
        properties: {
          department: { type: 'string', description: 'Optional department slug (e.g. "gtm", "strategy", "finance", "agents").' },
          name: { type: 'string', description: 'Persona slug or full name (e.g. "april-dunford").' },
          query: { type: 'string', description: 'Keyword search across domains, cells, and archetypes.' },
          limit: { type: 'integer', minimum: 1, maximum: 20, description: 'Maximum search matches (default 5).' },
        },
        additionalProperties: false,
      },
    },
    {
      name: 'coco_board',
      description: 'Assemble a Super Intelligence advisory board (persona cards + structured debate protocol, zero model/network calls).',
      annotations: readOnlyAnnotations,
      inputSchema: {
        type: 'object',
        properties: {
          question: { type: 'string', description: 'Decision or question to convene the advisory board on.' },
          departments: {
            type: 'array', items: { type: 'string' },
            description: 'Optional department slugs (e.g. ["gtm", "finance", "strategy"]). Auto-selects top departments when omitted.',
          },
          size: { type: 'integer', minimum: 1, maximum: 16, description: 'Optional total persona cards to seat.' },
          max_departments: { type: 'integer', minimum: 1, maximum: 13, description: 'Departments to select when auto-routing (default 3).' },
          per_department: { type: 'integer', minimum: 1, maximum: 4, description: 'Personas per department when size is omitted (default 1).' },
          verb: { type: 'string', description: 'Optional SI verb (e.g. "Decide", "Analyse", "Tradeoff", "Stress-Test").' },
        },
        required: ['question'],
        additionalProperties: false,
      },
    },
  ];
}

module.exports = { buildSiIndex, buildPromptIndex, callPersona, callBoard, readPersonaResource, getPrompt, siTools };
