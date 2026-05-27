#!/usr/bin/env node
/**
 * Axe-core WCAG 2.1 AA scanner.
 *
 * Visits each of the 16 main routes, runs axe-core, dumps JSON to disk,
 * and prints a per-rule summary (critical/serious/moderate/minor) so we
 * can target the top violations for fixes.
 *
 * Usage:  node scripts/axe-scan.mjs [--out path/to/report.json]
 */
import { chromium } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';

const BASE = process.env.AXE_BASE_URL || 'http://localhost:5173';
const OUT =
  process.argv.find((a) => a.startsWith('--out='))?.split('=')[1] ||
  'axe-report.json';

// The 16 main pages of the platform. ProjectDetail uses a stub id we know
// will route successfully (route exists; page renders error-boundary safe).
const ROUTES = [
  { name: 'Home', path: '/' },
  { name: 'Analytics', path: '/analytics' },
  { name: 'Projects', path: '/projects' },
  { name: 'ProjectDetail', path: '/projects/demo' },
  { name: 'Agents', path: '/agents' },
  { name: 'Knowledge', path: '/knowledge' },
  { name: 'Brain', path: '/brain' },
  { name: 'Graph', path: '/graph' },
  { name: 'Inbox', path: '/inbox' },
  { name: 'Todos', path: '/todos' },
  { name: 'Drafts', path: '/drafts' },
  { name: 'Goals', path: '/goals' },
  { name: 'Chat', path: '/chat' },
  { name: 'Costs', path: '/costs' },
  { name: 'Activity', path: '/activity' },
  { name: 'Settings', path: '/settings' },
];

async function run() {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  // Silence noisy app console errors — we care about a11y, not fetch fails.
  page.on('pageerror', () => {});

  const report = { base: BASE, generatedAt: new Date().toISOString(), routes: [] };
  const ruleAgg = new Map(); // rule -> { count, impact, help, helpUrl, routes:Set }

  for (const r of ROUTES) {
    const url = BASE + r.path;
    process.stdout.write(`scan ${r.name.padEnd(15)} ${url} ... `);
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
      // Give the app a tick to settle async data.
      await page.waitForTimeout(800);
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();
      const v = results.violations;
      const byImpact = v.reduce((m, x) => ({ ...m, [x.impact || 'none']: (m[x.impact || 'none'] || 0) + 1 }), {});
      console.log(`${v.length} violations`, JSON.stringify(byImpact));
      report.routes.push({
        route: r.name,
        path: r.path,
        url,
        violationCount: v.length,
        byImpact,
        violations: v.map((x) => ({
          id: x.id,
          impact: x.impact,
          help: x.help,
          helpUrl: x.helpUrl,
          nodes: x.nodes.slice(0, 5).map((n) => ({
            target: n.target,
            html: n.html.slice(0, 240),
            failureSummary: n.failureSummary,
          })),
        })),
      });
      for (const x of v) {
        const slot = ruleAgg.get(x.id) || {
          rule: x.id,
          impact: x.impact,
          help: x.help,
          helpUrl: x.helpUrl,
          nodeCount: 0,
          routes: new Set(),
        };
        slot.nodeCount += x.nodes.length;
        slot.routes.add(r.name);
        ruleAgg.set(x.id, slot);
      }
    } catch (e) {
      console.log('ERR', e.message);
      report.routes.push({ route: r.name, path: r.path, url, error: e.message });
    }
  }

  const ruleSummary = [...ruleAgg.values()]
    .map((s) => ({ ...s, routes: [...s.routes] }))
    .sort((a, b) => b.nodeCount - a.nodeCount);
  report.ruleSummary = ruleSummary;
  report.totals = report.routes.reduce(
    (acc, r) => {
      if (!r.byImpact) return acc;
      for (const k of Object.keys(r.byImpact)) acc[k] = (acc[k] || 0) + r.byImpact[k];
      acc.total = (acc.total || 0) + (r.violationCount || 0);
      return acc;
    },
    {},
  );

  fs.mkdirSync(path.dirname(path.resolve(OUT)), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));

  console.log('\n=== Rule summary (top 20 by node count) ===');
  for (const s of ruleSummary.slice(0, 20)) {
    console.log(
      `${String(s.nodeCount).padStart(4)}  ${String(s.impact || '').padEnd(8)}  ${s.rule.padEnd(40)}  (${s.routes.length} routes)`,
    );
  }
  console.log('\n=== Totals ===');
  console.log(JSON.stringify(report.totals, null, 2));
  console.log(`\nWrote ${OUT}`);

  await browser.close();
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
