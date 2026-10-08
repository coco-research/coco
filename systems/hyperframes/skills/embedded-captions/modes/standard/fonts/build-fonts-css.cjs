#!/usr/bin/env node
/*
 * build-fonts-css.cjs — bundle the template fonts into ONE self-contained
 * fonts.css with base64 data-URI @font-face (no sub-resources, no CDN, no
 * system-font dependency). This is what makes Standard/Cinematic renders
 * deterministic on ANY machine: hyperframes' renderer only auto-supplies its
 * ~18 CANONICAL_FONTS; every other family falls back to a generic font unless
 * the HTML ships a local @font-face. (hyperframes' own font linter says exactly
 * this: "Use local @font-face declarations with captured .woff2 files.")
 *
 * Source woff2 live in ./files/<slug>-latin-<weight>-normal.woff2 (latin subset
 * from @fontsource via jsdelivr). Re-run after adding/removing a font:
 *   node build-fonts-css.cjs
 *
 * Modified by Coco, 2026-10-08 (lab-0062): a family whose OFL declares a
 * Reserved Font Name may not ship as a subset (a subset is a Modified
 * Version), so those families ship as the UNMODIFIED google/fonts TTF listed
 * in UPSTREAM below. Each is embedded as-is (font/ttf) and its sha256 is
 * checked on every build; a subset woff2 for one of them is refused.
 */
const fs = require("fs");
const path = require("path");

const FILES = path.join(__dirname, "files");
const OUT = path.join(__dirname, "fonts.css");

// slug → exact CSS family name (must match what templates declare in font-family).
const FAMILY = {
  anton: "Anton",
  audiowide: "Audiowide",
  inter: "Inter",
  "baloo-2": "Baloo 2",
  bangers: "Bangers",
  "bodoni-moda": "Bodoni Moda",
  caveat: "Caveat",
  cinzel: "Cinzel",
  "cormorant-garamond": "Cormorant Garamond",
  creepster: "Creepster",
  fredoka: "Fredoka",
  monoton: "Monoton",
  orbitron: "Orbitron",
  "permanent-marker": "Permanent Marker",
  "press-start-2p": "Press Start 2P",
  "saira-stencil-one": "Saira Stencil One",
  "shippori-mincho": "Shippori Mincho",
  rajdhani: "Rajdhani",
  "chakra-petch": "Chakra Petch",
  sora: "Sora",
  "space-grotesk": "Space Grotesk",
  "special-elite": "Special Elite",
  teko: "Teko",
  vt323: "VT323",
};

// Unmodified upstream files: google/fonts @ 2eb0b48d5f760f62e286216f0859a8c540dbc1bd
// (https://github.com/google/fonts/tree/2eb0b48d5f760f62e286216f0859a8c540dbc1bd/ofl).
// These families' OFL texts reserve their names, so they are never subset here.
const UPSTREAM = {
  "Audiowide-Regular.ttf": {
    family: "Audiowide",
    weight: "400",
    style: "normal",
    sha256: "c7c0f2b0f6fad8c623e31772ce79f94a4edb9321ffce9fce978ea892d20ae730",
  },
  "Creepster-Regular.ttf": {
    family: "Creepster",
    weight: "400",
    style: "normal",
    sha256: "402aeb734586c74aecd3dbdc454589b1fb12e2e1c71f782fd019ae68066d9f44",
  },
  "Monoton-Regular.ttf": {
    family: "Monoton",
    weight: "400",
    style: "normal",
    sha256: "951c4cea65ffede784a7c9672feec5d329a7e1e12216c42d53ecf36c90d04dea",
  },
  // variable font (wght 400-900): one file serves the 400 and 700 the templates use
  "Orbitron[wght].ttf": {
    family: "Orbitron",
    weight: "400 900",
    style: "normal",
    sha256: "f42db2dd16e642258e35782916eceb1dcdbea06fb958d77ad71dc5963587e8fd",
  },
  "PressStart2P-Regular.ttf": {
    family: "Press Start 2P",
    weight: "400",
    style: "normal",
    sha256: "034c77f1f05ec89421e4a63f0e3a4ca1ecf852cc6d2bf611f126f275728e017d",
  },
};
const RESERVED = new Set(Object.values(UPSTREAM).map((u) => u.family));

const files = fs
  .readdirSync(FILES)
  .filter((f) => f.endsWith(".woff2") || f.endsWith(".ttf"))
  .sort();
const faces = [];
let raw = 0;
const seenFamilies = new Set();
for (const f of files) {
  if (f.endsWith(".ttf")) {
    const u = UPSTREAM[f];
    if (!u) {
      console.error(`[fonts] ${f} is not a pinned upstream file — add it to UPSTREAM`);
      process.exit(1);
    }
    const buf = fs.readFileSync(path.join(FILES, f));
    const sha = require("crypto").createHash("sha256").update(buf).digest("hex");
    if (sha !== u.sha256) {
      console.error(`[fonts] ${f}: sha256 ${sha} != pinned upstream ${u.sha256} (file was modified?)`);
      process.exit(1);
    }
    raw += buf.length;
    seenFamilies.add(u.family);
    faces.push(
      `@font-face {\n` +
        `  font-family: '${u.family}';\n` +
        `  font-style: ${u.style};\n` +
        `  font-weight: ${u.weight};\n` +
        `  font-display: block;\n` +
        `  src: url(data:font/ttf;base64,${buf.toString("base64")}) format('truetype');\n` +
        `}`,
    );
    continue;
  }
  const m = f.match(/^(.*)-latin-(\d+)-(normal|italic)\.woff2$/);
  if (!m) {
    console.error(`[fonts] skip unrecognized filename: ${f}`);
    continue;
  }
  const slug = m[1],
    weight = m[2],
    style = m[3];
  const family = FAMILY[slug];
  if (!family) {
    console.error(`[fonts] no family mapping for slug "${slug}" (${f}) — add it to FAMILY`);
    process.exit(1);
  }
  if (RESERVED.has(family)) {
    console.error(
      `[fonts] ${f}: "${family}" has a Reserved Font Name; ship the unmodified upstream file, not a subset`,
    );
    process.exit(1);
  }
  const buf = fs.readFileSync(path.join(FILES, f));
  raw += buf.length;
  seenFamilies.add(family);
  faces.push(
    `@font-face {\n` +
      `  font-family: '${family}';\n` +
      `  font-style: ${style};\n` +
      `  font-weight: ${weight};\n` +
      `  font-display: block;\n` + // block (not swap): render text only once the real face is ready — measure-layout + capture see the true glyphs, never a fallback flash
      `  src: url(data:font/woff2;base64,${buf.toString("base64")}) format('woff2');\n` +
      `}`,
  );
}

const header =
  `/* AUTO-GENERATED by build-fonts-css.cjs — do not edit by hand.\n` +
  `   ${faces.length} faces / ${seenFamilies.size} families, ${Math.round(raw / 1024)}KB raw (base64-inlined).\n` +
  `   woff2 faces are latin subsets; families with a Reserved Font Name are the\n` +
  `   unmodified google/fonts TTF (sha256-checked, see UPSTREAM in the generator).\n` +
  `   Families: ${[...seenFamilies].sort().join(", ")}.\n` +
  `   These are the template fonts NOT in hyperframes' auto-resolved set; inlining\n` +
  `   them makes every render deterministic regardless of installed system fonts. */\n`;

fs.writeFileSync(OUT, header + "\n" + faces.join("\n\n") + "\n");
const outKb = Math.round(fs.statSync(OUT).size / 1024);
console.log(`[fonts] wrote ${OUT}`);
console.log(
  `[fonts] ${faces.length} faces, ${seenFamilies.size} families, ${outKb}KB css (${Math.round(raw / 1024)}KB raw)`,
);
console.log(`[fonts] families: ${[...seenFamilies].sort().join(", ")}`);
