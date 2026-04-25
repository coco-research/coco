---
name: clone-website
description: Clone any website into a pixel-perfect single-file HTML prototype. Extracts design tokens, assets, CSS computed styles, interaction patterns, and content via Playwright. Outputs a self-contained HTML file with real data injection. Use when the user wants to clone, replicate, reverse-engineer, or create a pixel-perfect copy of any website or web app. Provide one or more target URLs as arguments.
argument-hint: "<url1> [<url2> ...]"
user-invocable: true
---

# Clone Website --- Single-File HTML Prototype Builder

You are about to reverse-engineer **$ARGUMENTS** into a pixel-perfect single-file HTML prototype.

This is adapted from the [ai-website-cloner-template](https://github.com/JCodesMore/ai-website-cloner-template) approach but optimized for rapid prototyping workflows: **single self-contained HTML files** (no build system, no CDN dependencies, opens directly in a browser).

## Output Format

Unlike the original repo (Next.js + shadcn/ui), our output is:
- **One HTML file** with `<style>` + `<body>` + `<script>` sections
- **Zero external dependencies** --- all CSS inline, all JS inline, all assets base64-encoded or SVG inline
- **Real data injection** --- not lorem ipsum, but actual data from project Excel files, meeting notes, and brain DB
- **Project design system** when available --- use tokens from a `design-system.json` colocated with the project

## Pre-Flight

1. **Playwright is required.** Verify: `npx playwright --version`. If not installed, ask the user to run `npm i -D playwright`.
2. Parse `$ARGUMENTS` as one or more URLs. Validate each is accessible.
3. Create output directory: `{project}/Screenshots-clone/` for captured assets.
4. Determine clone mode:
   - **Full clone** (default): pixel-perfect reproduction of the entire page
   - **Design extraction only** (`--extract`): capture design tokens, screenshots, and component specs without building
   - **Selective clone** (`--sections "header,table,sidebar"`): clone only named sections

## Phase 1: Reconnaissance (Playwright)

### 1.1 Screenshots

Use Playwright to capture:

```javascript
import { chromium } from 'playwright';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(URL);

// Full page screenshot
await page.screenshot({ path: 'full-desktop.png', fullPage: true });

// Viewport screenshot
await page.screenshot({ path: 'viewport-desktop.png' });

// Mobile
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({ path: 'viewport-mobile.png', fullPage: true });
```

### 1.2 Design Token Extraction

Run this in Playwright's `page.evaluate()` to extract the complete design system:

```javascript
const tokens = await page.evaluate(() => {
  // Colors
  const colorMap = new Map();
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    ['color','backgroundColor','borderColor','borderTopColor','borderBottomColor'].forEach(p => {
      const v = cs[p];
      if (v && v !== 'rgba(0, 0, 0, 0)' && v !== 'transparent') colorMap.set(v, (colorMap.get(v)||0)+1);
    });
  });

  // Typography
  const fontMap = new Map();
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    const key = `${cs.fontFamily}|${cs.fontSize}|${cs.fontWeight}|${cs.lineHeight}`;
    fontMap.set(key, (fontMap.get(key)||0)+1);
  });

  // Spacing
  const spacingSet = new Set();
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    ['padding','margin','gap'].forEach(p => {
      const v = cs[p]; if (v && v !== '0px') spacingSet.add(v);
    });
  });

  // Shadows
  const shadowSet = new Set();
  document.querySelectorAll('*').forEach(el => {
    const v = getComputedStyle(el).boxShadow;
    if (v && v !== 'none') shadowSet.add(v);
  });

  // Radius
  const radiusSet = new Set();
  document.querySelectorAll('*').forEach(el => {
    const v = getComputedStyle(el).borderRadius;
    if (v && v !== '0px') radiusSet.add(v);
  });

  return {
    colors: [...colorMap.entries()].sort((a,b) => b[1]-a[1]).slice(0,30),
    typography: [...fontMap.entries()].sort((a,b) => b[1]-a[1]).slice(0,20),
    spacing: [...spacingSet].sort(),
    shadows: [...shadowSet],
    radii: [...radiusSet].sort()
  };
});
```

### 1.3 Component CSS Extraction (Deep)

For each major component/section, extract exact computed styles:

```javascript
// Run per component container
const componentCSS = await page.evaluate((selector) => {
  const el = document.querySelector(selector);
  if (!el) return null;
  const props = [
    'fontSize','fontWeight','fontFamily','lineHeight','letterSpacing','color',
    'textTransform','textDecoration','backgroundColor','background',
    'padding','paddingTop','paddingRight','paddingBottom','paddingLeft',
    'margin','marginTop','marginRight','marginBottom','marginLeft',
    'width','height','maxWidth','minWidth','display','flexDirection',
    'justifyContent','alignItems','gap','gridTemplateColumns',
    'borderRadius','border','boxShadow','overflow','position',
    'top','right','bottom','left','zIndex','opacity','transform','transition'
  ];
  function extract(element, depth) {
    if (depth > 4) return null;
    const cs = getComputedStyle(element);
    const styles = {};
    props.forEach(p => {
      const v = cs[p];
      if (v && v !== 'none' && v !== 'normal' && v !== 'auto' && v !== '0px' && v !== 'rgba(0, 0, 0, 0)')
        styles[p] = v;
    });
    return {
      tag: element.tagName.toLowerCase(),
      classes: element.className?.toString().split(' ').slice(0,5).join(' '),
      text: element.childNodes.length === 1 && element.childNodes[0].nodeType === 3
        ? element.textContent.trim().slice(0,200) : null,
      styles,
      children: [...element.children].slice(0,20).map(c => extract(c, depth+1)).filter(Boolean)
    };
  }
  return extract(el, 0);
}, selector);
```

### 1.4 Interaction Sweep

Use Playwright to discover behaviors:

```javascript
// Scroll sweep
for (let y = 0; y < await page.evaluate(() => document.body.scrollHeight); y += 300) {
  await page.evaluate(y => window.scrollTo(0, y), y);
  await page.waitForTimeout(200);
  // Check for sticky header changes, scroll-triggered animations, etc.
}

// Hover sweep --- hover over interactive elements
const interactiveEls = await page.$$('button, a, [role="tab"], .nav-item, .card');
for (const el of interactiveEls.slice(0, 30)) {
  await el.hover();
  await page.waitForTimeout(100);
}

// Click sweep --- test tabs, dropdowns, etc.
const tabs = await page.$$('[role="tab"], .tab-item, .nav-tab');
for (const tab of tabs) {
  await tab.click();
  await page.waitForTimeout(300);
}
```

### 1.5 Asset Extraction

```javascript
// Extract all SVG icons as inline code
const svgs = await page.evaluate(() =>
  [...document.querySelectorAll('svg')].map(s => ({
    html: s.outerHTML,
    parent: s.parentElement?.className?.toString().split(' ')[0] || 'unknown',
    width: s.getAttribute('width'),
    height: s.getAttribute('height')
  }))
);

// Extract all image URLs for download
const images = await page.evaluate(() =>
  [...document.querySelectorAll('img')].map(i => ({
    src: i.src, alt: i.alt, w: i.naturalWidth, h: i.naturalHeight
  }))
);
```

## Phase 2: Foundation Build

Convert extracted tokens into CSS custom properties:

```css
:root {
  /* Colors --- from extraction, mapped to semantic names */
  --color-bg: {extracted};
  --color-text: {extracted};
  --color-text-muted: {extracted};
  --color-accent: {extracted};
  --color-border: {extracted};
  /* ... */

  /* Typography */
  --font-family: {extracted};
  --font-size-body: {extracted};
  /* ... */

  /* Shadows */
  --shadow-sm: {extracted};
  --shadow-md: {extracted};
  /* ... */
}
```

## Phase 3: Parallel Section Building

For each major section of the page, dispatch a builder agent:

1. Write a spec file with exact CSS values + screenshot + content
2. Launch agent in a worktree (or as a subagent) with the spec
3. Each agent produces its section's HTML + CSS + JS
4. Orchestrator assembles all sections into one file

**Complexity budget**: If a section spec exceeds ~150 lines, split it.

## Phase 4: Assembly

Merge all sections into one self-contained HTML file:
1. Deduplicate CSS --- combine all section styles, remove duplicates
2. Order HTML --- sections in visual order (top to bottom)
3. Combine JS --- all event handlers and render functions in one `<script>` block
4. Base64-encode any images that couldn't be replaced with CSS/SVG
5. Verify: open in browser, compare against original screenshots

## Phase 5: Quality Check

Use Playwright to:
1. Open the built HTML file
2. Take screenshots at the same viewpoints as Phase 1
3. Compare side-by-side (save both for manual review)
4. Test all interactions (clicks, hovers, tabs)
5. Report any visual differences

## Project-Specific Mode

When a `design-system.json` exists in the project:
- Load tokens (colors, typography, spacing, shadows, radii) from that file
- Apply them as CSS custom properties in the output
- Inject any real data referenced in the project (Excel, JSON, brain DB)

## Reference

- Adapted from [JCodesMore/ai-website-cloner-template](https://github.com/JCodesMore/ai-website-cloner-template)
