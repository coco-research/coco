// Tests for build-fonts-css.cjs: every font file in files/ must be one the
// generator embeds and checks; odd or mislabelled files are errors, not warnings.
// Added by Coco, 2026-10-08 (lab-0062). Run: node --test build-fonts-css.test.cjs
// Modified by Coco, 2026-10-22 (#335): test licence text validation. See MODIFICATIONS.md.
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { build } = require("./build-fonts-css.cjs");

const FILES = path.join(__dirname, "files");

/** copy files/ into a temp dir, apply `mutate(dir)`, and return build()'s result or error */
function withCopy(mutate) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "fonts-test-"));
  try {
    for (const f of fs.readdirSync(FILES)) fs.copyFileSync(path.join(FILES, f), path.join(dir, f));
    mutate(dir);
    return build({ filesDir: dir });
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}
const cp = (dir, from, to) => fs.copyFileSync(path.join(FILES, from), path.join(dir, to));
const fails = (mutate, re) =>
  assert.throws(
    () => withCopy(mutate),
    (e) => {
      assert.match(e.message, re);
      return true;
    },
  );

test("the shipped files/ build cleanly", () => {
  const r = build();
  assert.strictEqual(r.faces, 43);
  assert.strictEqual(r.families.length, 24);
});

test("a reserved-family subset under another name is an error (Orbitron-Bold.woff2)", () => {
  fails(
    (d) => cp(d, "teko-latin-700-normal.woff2", "Orbitron-Bold.woff2"),
    /Orbitron-Bold\.woff2: unrecognized font file name/,
  );
});

test(".woff, .otf, .ttc and .eot files are errors, not silently ignored", () => {
  fails(
    (d) => cp(d, "inter-latin-400-normal.woff2", "inter-latin-400-normal.woff"),
    /inter-latin-400-normal\.woff: unrecognized/,
  );
  fails(
    (d) => cp(d, "Monoton-Regular.ttf", "Monoton-Regular.otf"),
    /Monoton-Regular\.otf: unrecognized/,
  );
  fails((d) => fs.writeFileSync(path.join(d, "x.ttc"), "not really"), /x\.ttc: unrecognized/);
  fails((d) => fs.writeFileSync(path.join(d, "x.eot"), ""), /x\.eot: unrecognized/);
});

test("a font disguised as a licence text or any other file is an error", () => {
  fails(
    (d) => cp(d, "teko-latin-400-normal.woff2", "OFL-extra.txt"),
    /OFL-extra\.txt: unrecognized font file name/,
  );
  fails(
    (d) => cp(d, "Audiowide-Regular.ttf", "notes.md"),
    /notes\.md: unrecognized font file name/,
  );
  fails((d) => fs.writeFileSync(path.join(d, "README.md"), "hi"), /README\.md: unexpected file/);
});

for (const [file, heading, other] of [
  ["OFL-anton.txt", "SIL OPEN FONT LICENSE Version 1.1", "Apache-2.0-permanent-marker.txt"],
  ["Apache-2.0-permanent-marker.txt", "Apache License\nVersion 2.0", "OFL-anton.txt"],
]) {
  test(`${file}: empty or whitespace-only licence text is refused`, () => {
    for (const text of ["", " \t\r\n"]) {
      fails(
        (d) => fs.writeFileSync(path.join(d, file), text),
        new RegExp(`${file}: licence must be non-empty UTF-8 text`),
      );
    }
  });

  test(`${file}: malformed UTF-8 is refused even with the correct heading`, () => {
    fails(
      (d) => fs.writeFileSync(
        path.join(d, file), Buffer.concat([Buffer.from([0xff]), Buffer.from(heading)]),
      ),
      new RegExp(`${file}: licence must be non-empty UTF-8 text`),
    );
  });

  test(`${file}: binary control bytes are refused even with the correct heading`, () => {
    fails(
      (d) => fs.writeFileSync(path.join(d, file), `${heading}\n\0\x01`),
      new RegExp(`${file}: licence must be non-empty UTF-8 text`),
    );
  });

  test(`${file}: missing or wrong licence heading is refused`, () => {
    fails(
      (d) => fs.writeFileSync(path.join(d, file), "This is not a licence."),
      new RegExp(`${file}: missing licence heading`),
    );
    fails((d) => cp(d, other, file), new RegExp(`${file}: missing licence heading`));
  });
}

test("valid UTF-8 licence texts with CRLF and heading whitespace build identically", () => {
  const r = withCopy((d) => {
    for (const file of ["OFL-anton.txt", "Apache-2.0-permanent-marker.txt"]) {
      const text = fs.readFileSync(path.join(d, file), "utf8");
      fs.writeFileSync(path.join(d, file), `Copyright ©\r\n${text.replace(/\s+/g, "\r\n\t")}`);
    }
  });
  assert.strictEqual(r.css, build().css);
});

test(".gitattributes is allowed without a licence heading", () => {
  const r = withCopy((d) => fs.writeFileSync(path.join(d, ".gitattributes"), "*.woff2 binary\n"));
  assert.strictEqual(r.css, build().css);
});

test("a subset whose name table names another family is an error", () => {
  fails(
    (d) => cp(d, "teko-latin-400-normal.woff2", "sora-latin-400-normal.woff2"),
    /sora-latin-400-normal\.woff2: its name table says family "Teko/,
  );
});

test("a subset whose OS/2 weight or italic flag differs from its file name is an error", () => {
  fails(
    (d) => cp(d, "inter-latin-400-normal.woff2", "inter-latin-700-normal.woff2"),
    /inter-latin-700-normal\.woff2: its OS\/2 weight is 400, but the file name says 700/,
  );
  fails(
    (d) => cp(d, "inter-latin-500-normal.woff2", "inter-latin-500-italic.woff2"),
    /inter-latin-500-italic\.woff2: its italic flag is false/,
  );
});

test("a subset of a Reserved-Font-Name family is refused", () => {
  fails(
    (d) => cp(d, "teko-latin-700-normal.woff2", "orbitron-latin-700-normal.woff2"),
    /Reserved Font Name; ship the unmodified upstream file/,
  );
});

test("a modified or unlisted upstream TTF is refused", () => {
  fails(
    (d) => fs.appendFileSync(path.join(d, "Monoton-Regular.ttf"), "\0"),
    /Monoton-Regular\.ttf: sha256 .* != pinned upstream/,
  );
  fails(
    (d) => cp(d, "Monoton-Regular.ttf", "Monoton-Copy.ttf"),
    /Monoton-Copy\.ttf: unrecognized font file name/,
  );
});

test("an unknown slug, a non-woff2 payload and a missing licence text are errors", () => {
  fails(
    (d) => cp(d, "teko-latin-400-normal.woff2", "roboto-latin-400-normal.woff2"),
    /no family mapping for slug "roboto"/,
  );
  fails(
    (d) => cp(d, "Monoton-Regular.ttf", "sora-latin-400-normal.woff2"),
    /named \.woff2 but its contents are a sfnt font/,
  );
  fails((d) => fs.unlinkSync(path.join(d, "OFL-teko.txt")), /Teko: no licence text/);
});
