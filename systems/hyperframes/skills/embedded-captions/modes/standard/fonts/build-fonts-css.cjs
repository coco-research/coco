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
 * Every file in ./files/ must be a font this script embeds or a licence text
 * (OFL-<slug>.txt / Apache-2.0-<slug>.txt): any other font file, whatever its
 * extension, is an error, and a subset's own name table (family, OS/2 weight,
 * italic flag) must match its file name. Tests: build-fonts-css.test.cjs.
 */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const zlib = require("zlib");

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
const SLUG_OF = Object.fromEntries(Object.entries(FAMILY).map(([s, f]) => [f, s]));

// ---- font sniffing and name-table reading (no dependencies) ----
const FONT_EXT = /\.(woff2?|[ot]t[fc]|eot|dfont|pf[ab]|fon|fnt|bdf|pcf)$/i;
const LICENCE_TEXT = /^((OFL|Apache-2\.0)-[a-z0-9-]+\.txt|\.gitattributes)$/;
// Style and optical-size words that Fontsource's static instances append to
// name ID 1 (e.g. "Teko Light" for teko-latin-700, "Bodoni Moda 11pt").
const STYLE_WORD =
  /^(thin|hairline|extralight|ultralight|light|book|regular|normal|medium|semibold|demibold|bold|extrabold|ultrabold|black|heavy|italic|oblique|\d+pt)$/i;

/** exact family match after dropping trailing style words (never a prefix match) */
function familyMatches(d, family) {
  return [d.typoFamily, d.family].filter(Boolean).some((n) => {
    const words = n.split(/\s+/);
    while (words.length > 1 && STYLE_WORD.test(words[words.length - 1])) words.pop();
    return words.join(" ").toLowerCase() === family.toLowerCase();
  });
}
const SUBSET = /^([a-z0-9-]+)-latin-(\d{3})-(normal|italic)\.woff2$/;

function fontKind(buf) {
  const sig = buf.subarray(0, 4).toString("latin1");
  if (["wOF2", "wOFF", "OTTO", "true", "typ1", "ttcf"].includes(sig)) return sig;
  if (buf.length >= 4 && buf.readUInt32BE(0) === 0x00010000) return "sfnt";
  if (buf.length >= 36 && buf.readUInt16LE(34) === 0x504c) return "eot"; // EOT MagicNumber
  return null;
}

// WOFF2 known-table tags (index = flags & 0x3f), from the WOFF2 spec
const WOFF2_TAGS = (
  "cmap head hhea hmtx maxp name OS/2 post cvt  fpgm glyf loca prep CFF  VORG EBDT " +
  "EBLC gasp hdmx kern LTSH PCLT VDMX vhea vmtx BASE GDEF GPOS GSUB EBSC JSTF MATH " +
  "CBDT CBLC COLR CPAL SVG  sbix acnt avar bdat bloc bsln cvar fdsc feat fmtx fvar " +
  "gvar hsty just lcar mort morx opbd prop trak Zapf Silf Glat Gloc Feat Sill"
)
  .match(/.{4}\s?/g)
  .map((t) => t.slice(0, 4));

function base128(buf, pos) {
  let v = 0;
  for (let i = 0; i < 5; i++) {
    const b = buf[pos.p++];
    v = v * 128 + (b & 0x7f);
    if (!(b & 0x80)) return v;
  }
  throw new Error("bad UIntBase128");
}

/** tables of a single (non-collection) WOFF2 or sfnt font: { tag: Buffer } */
function tables(buf) {
  const kind = fontKind(buf);
  const out = {};
  if (kind === "wOF2") {
    if (buf.readUInt32BE(4) === 0x74746366) throw new Error("WOFF2 collection not supported");
    const n = buf.readUInt16BE(12);
    const pos = { p: 48 };
    const dir = [];
    let off = 0;
    for (let i = 0; i < n; i++) {
      const flags = buf[pos.p++];
      let tag = WOFF2_TAGS[flags & 0x3f];
      if ((flags & 0x3f) === 63) {
        tag = buf.toString("latin1", pos.p, pos.p + 4);
        pos.p += 4;
      }
      const orig = base128(buf, pos);
      const xf = (flags >> 6) & 3;
      const transformed = tag === "glyf" || tag === "loca" ? xf !== 3 : xf !== 0;
      const len = transformed ? base128(buf, pos) : orig;
      dir.push({ tag, off, len });
      off += len;
    }
    const data = zlib.brotliDecompressSync(buf.subarray(pos.p, pos.p + buf.readUInt32BE(20)));
    for (const t of dir) out[t.tag] = data.subarray(t.off, t.off + t.len);
    return out;
  }
  if (kind === "wOFF") {
    const n = buf.readUInt16BE(12);
    for (let i = 0; i < n; i++) {
      const r = 44 + 20 * i;
      const o = buf.readUInt32BE(r + 4),
        c = buf.readUInt32BE(r + 8),
        l = buf.readUInt32BE(r + 12);
      const raw = buf.subarray(o, o + c);
      out[buf.toString("latin1", r, r + 4)] = c < l ? zlib.inflateSync(raw) : raw;
    }
    return out;
  }
  if (kind === "sfnt" || kind === "OTTO" || kind === "true") {
    const n = buf.readUInt16BE(4);
    for (let i = 0; i < n; i++) {
      const r = 12 + 16 * i;
      out[buf.toString("latin1", r, r + 4)] = buf.subarray(
        buf.readUInt32BE(r + 8),
        buf.readUInt32BE(r + 8) + buf.readUInt32BE(r + 12),
      );
    }
    return out;
  }
  throw new Error(`cannot read a ${kind || "non-font"} file`);
}

/** { family, weight, italic } from the font's own tables */
function describe(buf) {
  const t = tables(buf);
  if (!t.name || !t["OS/2"]) throw new Error("no name or OS/2 table");
  const name = t.name;
  const count = name.readUInt16BE(2),
    str = name.readUInt16BE(4);
  const ids = {};
  for (let i = 0; i < count; i++) {
    const r = 6 + 12 * i;
    const pid = name.readUInt16BE(r),
      id = name.readUInt16BE(r + 6);
    const raw = name.subarray(
      str + name.readUInt16BE(r + 10),
      str + name.readUInt16BE(r + 10) + name.readUInt16BE(r + 8),
    );
    const s = pid === 1 ? raw.toString("latin1") : Buffer.from(raw).swap16().toString("utf16le");
    if (!(id in ids) || pid === 3) ids[id] = s.trim();
  }
  const os2 = t["OS/2"];
  return {
    family: ids[1] || "",
    typoFamily: ids[16] || "",
    weight: os2.readUInt16BE(4),
    italic: (os2.readUInt16BE(62) & 1) === 1,
  };
}

// ---- build ----
function build({ filesDir = FILES } = {}) {
  const errors = [];
  const faces = [];
  const families = new Set();
  let raw = 0;
  const entries = fs.readdirSync(filesDir).sort();
  const present = new Set(entries);
  for (const f of entries) {
    const p = path.join(filesDir, f);
    if (!fs.statSync(p).isFile()) {
      errors.push(`${f}: unexpected directory in files/`);
      continue;
    }
    const buf = fs.readFileSync(p);
    const kind = fontKind(buf);
    if (!kind && !FONT_EXT.test(f)) {
      if (!LICENCE_TEXT.test(f))
        errors.push(
          `${f}: unexpected file; files/ holds only embedded fonts and their OFL-/Apache-2.0- licence texts`,
        );
      continue;
    }
    const u = UPSTREAM[f];
    if (u) {
      const sha = crypto.createHash("sha256").update(buf).digest("hex");
      if (sha !== u.sha256) {
        errors.push(`${f}: sha256 ${sha} != pinned upstream ${u.sha256} (file was modified?)`);
        continue;
      }
      faces.push({
        family: u.family,
        style: u.style,
        weight: u.weight,
        mime: "font/ttf",
        format: "truetype",
        buf,
      });
      continue;
    }
    const m = f.match(SUBSET);
    if (!m) {
      errors.push(
        `${f}: unrecognized font file name (expected <slug>-latin-<weight>-<style>.woff2, or a pinned upstream file listed in UPSTREAM); it would ship in files/ without being embedded or checked`,
      );
      continue;
    }
    const [, slug, weight, style] = m;
    const family = FAMILY[slug];
    if (!family) {
      errors.push(`${f}: no family mapping for slug "${slug}" — add it to FAMILY`);
      continue;
    }
    if (RESERVED.has(family)) {
      errors.push(
        `${f}: "${family}" has a Reserved Font Name; ship the unmodified upstream file, not a subset`,
      );
      continue;
    }
    if (kind !== "wOF2") {
      errors.push(
        `${f}: named .woff2 but its contents are ${kind ? `a ${kind} font` : "not a font"}`,
      );
      continue;
    }
    let d;
    try {
      d = describe(buf);
    } catch (e) {
      errors.push(`${f}: unreadable font (${e.message})`);
      continue;
    }
    if (!familyMatches(d, family))
      errors.push(
        `${f}: its name table says family "${d.typoFamily || d.family}", but the file name says "${family}"`,
      );
    if (String(d.weight) !== weight)
      errors.push(`${f}: its OS/2 weight is ${d.weight}, but the file name says ${weight}`);
    if (d.italic !== (style === "italic"))
      errors.push(`${f}: its italic flag is ${d.italic}, but the file name says ${style}`);
    faces.push({ family, style, weight, mime: "font/woff2", format: "woff2", buf });
  }
  for (const fam of new Set(faces.map((x) => x.family))) {
    const slug = SLUG_OF[fam];
    if (!present.has(`OFL-${slug}.txt`) && !present.has(`Apache-2.0-${slug}.txt`))
      errors.push(`${fam}: no licence text (OFL-${slug}.txt or Apache-2.0-${slug}.txt) in files/`);
  }
  if (errors.length) {
    const e = new Error(`[fonts] ${errors.length} problem(s) in files/:\n  ${errors.join("\n  ")}`);
    e.problems = errors;
    throw e;
  }
  const blocks = faces.map((x) => {
    raw += x.buf.length;
    families.add(x.family);
    return (
      `@font-face {\n` +
      `  font-family: '${x.family}';\n` +
      `  font-style: ${x.style};\n` +
      `  font-weight: ${x.weight};\n` +
      `  font-display: block;\n` + // block (not swap): render text only once the real face is ready — measure-layout + capture see the true glyphs, never a fallback flash
      `  src: url(data:${x.mime};base64,${x.buf.toString("base64")}) format('${x.format}');\n` +
      `}`
    );
  });
  const header =
    `/* AUTO-GENERATED by build-fonts-css.cjs — do not edit by hand.\n` +
    `   ${faces.length} faces / ${families.size} families, ${Math.round(raw / 1024)}KB raw (base64-inlined).\n` +
    `   woff2 faces are latin subsets; families with a Reserved Font Name are the\n` +
    `   unmodified google/fonts TTF (sha256-checked, see UPSTREAM in the generator).\n` +
    `   Families: ${[...families].sort().join(", ")}.\n` +
    `   These are the template fonts NOT in hyperframes' auto-resolved set; inlining\n` +
    `   them makes every render deterministic regardless of installed system fonts. */\n`;
  return {
    css: header + "\n" + blocks.join("\n\n") + "\n",
    faces: faces.length,
    families: [...families].sort(),
    raw,
  };
}

module.exports = { build, describe, familyMatches, fontKind, FAMILY, UPSTREAM };

if (require.main === module) {
  let r;
  try {
    r = build();
  } catch (e) {
    console.error(e.message);
    process.exit(1);
  }
  fs.writeFileSync(OUT, r.css);
  const outKb = Math.round(fs.statSync(OUT).size / 1024);
  console.log(`[fonts] wrote ${OUT}`);
  console.log(
    `[fonts] ${r.faces} faces, ${r.families.length} families, ${outKb}KB css (${Math.round(r.raw / 1024)}KB raw)`,
  );
  console.log(`[fonts] families: ${r.families.join(", ")}`);
}
