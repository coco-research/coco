#!/usr/bin/env python3
"""Planted cases for scripts/check-personas.py rules (e), (i), (j), (k), --all and --links.

Everything here is offline:
- each case builds a small board in a temp folder (a copy of the checker, the
  label template, a strategy and a gtm department) and plants one problem;
- --links runs with name resolution and fetching stubbed, never the network;
- --all runs over the real board with socket connections made to raise;
- the input-safety cases (long input, symlinks, stalled hops) use invented
  people and a fabricated sentinel file beside the fake board.

Run from repo root: python3 tests/check-personas-rules-test.py
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check-personas.py"
GOOD = ROOT / "tests" / "fixtures" / "personas" / "edtech" / "personas" / "good.md"
GTM = "systems/superintelligence/gtm/personas/"
failures = 0


def expect(ok, what, detail=""):
    global failures
    print(f"  {'PASS' if ok else 'FAIL'}: {what}")
    if not ok:
        failures += 1
        if detail:
            print("    " + str(detail).strip().replace("\n", "\n    "))


def sha(name):
    return hashlib.sha256(" ".join(name.casefold().split()).encode()).hexdigest()


def persona(slug, name, fm="", body=""):
    text = re.sub(r"^slug: .*$", f"slug: {slug}", GOOD.read_text(encoding="utf-8"), count=1, flags=re.M)
    text = re.sub(r"^real_name: .*$", lambda _: f"real_name: {name}{fm}", text, count=1, flags=re.M)
    return text + body


def board(tmp, gtm, optout="# sha256 of the case-folded, space-collapsed real_name, one per line\n", extra=None):
    """A temp repo: the checker, the label template, strategy/strategy-example, the gtm files and any extra departments."""
    (tmp / "scripts").mkdir()
    shutil.copy(CHECK, tmp / "scripts" / "check-personas.py")
    (tmp / "systems/superintelligence/templates").mkdir(parents=True)
    shutil.copy(ROOT / "systems/superintelligence/templates/attribution.md", tmp / "systems/superintelligence/templates")
    for dept, people in (("strategy", {"strategy-example": ("strategy-example", "Strategy Example", "", "")}),
                         ("gtm", gtm), *(extra or {}).items()):
        d = tmp / "systems/superintelligence" / dept / "personas"
        d.mkdir(parents=True)
        (d.parent / "registry.json").write_text(json.dumps({"personas": {v[0]: {"slug": v[0]} for v in people.values()}}))
        for file, (slug, name, fm, body) in people.items():
            (d / f"{file}.md").write_text(persona(slug, name, fm, body), encoding="utf-8")
    if optout is not None:
        (tmp / "docs/personas").mkdir(parents=True)
        (tmp / "docs/personas/optout.sha256").write_text(optout)


def run(gtm, files, optout=None, args=(), extra=None):
    """files: gtm file names, or "<dept>/<file>" for an extra department."""
    with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
        tmp = Path(t)
        if optout is None:
            board(tmp, gtm, extra=extra)
        else:
            board(tmp, gtm, optout, extra)
        paths = [GTM + f + ".md" if "/" not in f else "systems/superintelligence/%s/personas/%s.md" % tuple(f.split("/"))
                 for f in files]
        p = subprocess.run([sys.executable, "scripts/check-personas.py", *args, *paths],
                           cwd=tmp, capture_output=True, text=True)
        return p.returncode, p.stdout.splitlines(), p.stderr.strip()


OPTED = "# sha256 of the case-folded, space-collapsed real_name\n" + sha("Opted Out Person") + "\n"
CLEAN = ("clean-example", "Clean Example", "", "")

# One planted file trips (i), (j) and (k); only those three lines, exit 1.
planted = ("planted-example", "Opted Out Person", "\naliases: [Strategy Example]", "\n\nOffice line: 415-555-0134\n")
code, out, err = run({"planted-example": planted, "clean-example": CLEAN}, ["planted-example", "clean-example"], OPTED)
line = persona(*planted).split("\n").index("Office line: 415-555-0134") + 1
want = [
    f"{GTM}planted-example.md: (i) duplicate: name also used by strategy/personas/strategy-example.md",
    f"{GTM}planted-example.md: (j) opted-out: this person asked not to be included (docs/personas/TAKEDOWN.md)",
    f"{GTM}planted-example.md: (k) private-detail: line {line} looks like a phone number",
]
expect(code == 1 and out == want and err == "check-personas: 1/2 pass",
       "planted duplicate, opted-out name and phone number print those 3 lines, exit 1",
       f"exit {code}\n" + "\n".join(out) + "\n" + err)

# (i) duplicate: slug, real_name and aliases, case-folded, across departments.
for case, gtm_file, want_line in (
    ("slug", ("strategy-example", "Slug Twin", "", ""), "(i) duplicate: slug also used by strategy/personas/strategy-example.md"),
    ("case-folded name", ("name-twin", "STRATEGY   example", "", ""), "(i) duplicate: name also used by strategy/personas/strategy-example.md"),
    ("alias", ("alias-twin", "Alias Twin", "\naliases: [strategy example]", ""), "(i) duplicate: name also used by strategy/personas/strategy-example.md"),
):
    code, out, _ = run({"twin": gtm_file}, ["twin"])
    expect(code == 1 and out == [f"{GTM}twin.md: {want_line}"], f"(i) fires on a duplicate {case}", "\n".join(out))
code, out, _ = run({"clean-example": CLEAN}, ["clean-example"])
expect(code == 0 and out == [], "(i) stays quiet on a unique name", "\n".join(out))

# (i) grandfathered two-team seats: only that slug, only in those two departments.
WU = ("tim-wu", "Tim Wu", "", "")
SEAT = {"legal-ip": {"tim-wu": WU}, "risk-compliance": {"tim-wu": WU}}
code, out, _ = run({}, ["legal-ip/tim-wu", "risk-compliance/tim-wu"], extra=SEAT)
expect(code == 0 and out == [], "(i) allows a grandfathered two-team seat (legal-ip + risk-compliance)", "\n".join(out))
code, out, _ = run({"tim-wu": WU}, ["tim-wu"], extra=SEAT)
expect(code == 1 and len(out) == 2 and all(" (i) duplicate: slug and name also used by " in l for l in out),
       "(i) fires on a grandfathered seat in a third department", "\n".join(out))
code, out, _ = run({}, ["risk-compliance/timothy-wu"],
                   extra={"legal-ip": {"tim-wu": WU}, "risk-compliance": {"timothy-wu": ("timothy-wu", "Tim Wu", "", "")}})
expect(code == 1 and out == ["systems/superintelligence/risk-compliance/personas/timothy-wu.md: "
                             "(i) duplicate: name also used by legal-ip/personas/tim-wu.md"],
       "(i) fires on a grandfathered person under a different slug", "\n".join(out))
code, out, _ = run({}, ["risk-compliance/new-twin"],
                   extra={"legal-ip": {"new-twin": ("new-twin", "New Twin", "", "")},
                          "risk-compliance": {"new-twin": ("new-twin", "New Twin", "", "")}})
expect(code == 1 and out == ["systems/superintelligence/risk-compliance/personas/new-twin.md: "
                             "(i) duplicate: slug and name also used by legal-ip/personas/new-twin.md"],
       "(i) fires on a new cross-department duplicate in the same two departments", "\n".join(out))

# (e) quote: [extrapolated] counts like [paraphrase]; an untagged quote still fails.
LABEL = re.search(r"\*\*<Name> persona\*\*: [^\n]*",
                  (ROOT / "systems/superintelligence/templates/attribution.md").read_text(encoding="utf-8")).group(0)
for case, tag, want in (("tagged [extrapolated] passes", " [extrapolated]", []), ("untagged still fails", "", ["e"])):
    body = f"\n\n{LABEL.replace('<Name>', 'Quote Example')}\n\n> \"A simulated reply.\"{tag}\n"
    code, out, _ = run({"q": ("q", "Quote Example", "", body)}, ["q"])
    expect(code == (1 if want else 0) and [l.split(": ", 1)[1][1] for l in out] == want, f"(e) a quote {case}", "\n".join(out))

# (j) opted-out: the hash of the normalized real_name; a missing list is empty; a bad list stops.
code, out, _ = run({"o": ("o", "  opted   OUT person", "", "")}, ["o"], OPTED)
expect(code == 1 and out == [f"{GTM}o.md: (j) opted-out: this person asked not to be included (docs/personas/TAKEDOWN.md)"],
       "(j) fires on a case and space variant of an opted-out name", "\n".join(out))
code, out, _ = run({"o": ("o", "Opted Out Person", "", "")}, ["o"], "")
expect(code == 0 and out == [], "(j) an empty list opts no one out", "\n".join(out))
with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
    board(Path(t), {"o": ("o", "Opted Out Person", "", "")}, optout=None)
    p = subprocess.run([sys.executable, "scripts/check-personas.py", GTM + "o.md"], cwd=t, capture_output=True, text=True)
    expect(p.returncode == 0 and p.stdout == "", "(j) a missing optout.sha256 counts as an empty list", p.stdout + p.stderr)
code, out, err = run({"o": ("o", "Opted Out Person", "", "")}, ["o"], "Opted Out Person\n")
expect(code == 2 and "not a sha256 hex line" in err, "(j) a plain-text line in optout.sha256 stops with exit 2", err)
# A malformed row may be a plain name: the message carries the line number, never the row.
for case, rows, n in (("a plain name", "Secret Nameson\n", 1),
                      ("a name after a comment, a blank and a good row", f"# note\n\n{sha('Someone Else')}\nSecret Nameson\n", 4),
                      ("a 63-digit hash", "a" * 63 + "\n", 1), ("a hash with trailing text", sha("A B") + " Secret\n", 1)):
    code, out, err = run({"o": ("o", "Opted Out Person", "", "")}, ["o"], rows)
    expect(code == 2 and err.endswith(f": line {n} is not a sha256 hex line") and "Secret" not in err,
           f"(j) {case} stops with exit 2 naming line {n}, never the row", err)
# A comment-only or blank file is an explicit empty list (a missing one is tested above).
for case, rows in (("a comment-only file", "# nobody has opted out yet\n"), ("a file of blank lines", "\n  \n")):
    code, out, _ = run({"o": ("o", "Opted Out Person", "", "")}, ["o"], rows)
    expect(code == 0 and out == [], f"(j) {case} is an explicit empty list", "\n".join(out))
# (a) real_name is one text value: a list or mapping is never hashed, so it would dodge (j).
for case, name, fm in (("a flow list", "[Opted Out Person]", ""), ("a block list", "", "\n  - Opted Out Person"),
                       ("a mapping", "{first: Opted, last: Person}", ""), ("only spaces", '"   "', "")):
    code, out, _ = run({"o": ("o", name, fm, "")}, ["o"], OPTED)
    expect(code == 1 and out == [f"{GTM}o.md: (a) frontmatter: real_name must be one non-empty text value"],
           f"(a) fails a real_name that is {case}, so (j) cannot be skipped", "\n".join(out))

# A quoted name followed by a comment is still the name: its quotes are not part of the value that gets hashed.
for case, name in (("double quotes and a comment", '"Opted Out Person" # reviewed'),
                   ("single quotes and a comment with an apostrophe", "'Opted Out Person' # it's fine")):
    code, out, _ = run({"o": ("o", name, "", "")}, ["o"], OPTED)
    expect(code == 1 and out == [f"{GTM}o.md: (j) opted-out: this person asked not to be included (docs/personas/TAKEDOWN.md)"],
           f"(j) catches an opted-out name written with {case}", "\n".join(out))

# (k) private-detail: phone, street address, personal email; near misses stay quiet.
for what, text in (("a street address", "Lives at 221 Baker Street, London."),
                   ("a personal email address", "Write to jane.doe@gmail.com for a reply."),
                   ("a phone number", "Call +44 20 7946 0958 after six.")):
    code, out, _ = run({"k": ("k", "Kay Example", "", f"\n\n{text}\n")}, ["k"])
    expect(code == 1 and len(out) == 1 and out[0].endswith(f"looks like {what}"), f"(k) fires on {what}", "\n".join(out))
quiet = "\n\nWork email jane@stanford.edu. ISBN 978-0-13-468599-1, arXiv 2101.12345, 2019-2023.\n" \
        "See https://example.com/call/415-555-0134 and doi 10.1145/3442188.3445922.\n"
code, out, _ = run({"k": ("k", "Kay Example", "", quiet)}, ["k"])
expect(code == 0 and out == [], "(k) stays quiet on a work email, ISBN, arXiv id, year range, URL and DOI", "\n".join(out))
# (k) also reads what a URL used to hide (its decoded path and query), upper-case and short-suffix street
# addresses (the street word may be in any case, the name before it is Capitalized or ALL CAPS). Invented
# people only; the line prints the rule and the line number, never what matched.
for what, text, secret in (
        ("a personal email address", "See https://example.com/contact?email=jane.doe%40gmail.com for her.", "jane"),
        ("a phone number", "See https://example.com/card?tel=%2B1%20415%20555%200134 for her.", "415"),
        ("a phone number", "See www.example.com/card?tel=415-555-0134 for her.", "415"),
        *(("a street address", f"Lives at {a}, London.", max(a.split()[1:-1], key=len).lower()) for a in (
            "221 BAKER STREET", "221 Baker St", "12 Elm Rd", "10 Orchard rd.", "1600 Maple Ave.", "350 Oak Blvd", "7 Pine Ln",
            "5 Elm Dr", "9 Hill Ct", "4 Privet Drive", "123 N Main St", "10 Sample St."))):
    code, out, _ = run({"k": ("k", "Kay Example", "", f"\n\n{text}\n")}, ["k"])
    expect(code == 1 and len(out) == 1 and out[0].endswith(f"looks like {what}") and secret not in out[0].lower(),
           f"(k) fires on {what}: {text[:44]}", "\n".join(out))
quiet_urls = ("\n\nSee https://example.com/contact?email=jane%40stanford.edu, https://doi.org/10.1145/3442188.3445922"
              " and https://en.wikipedia.org/wiki/Grant_Wiggins_(educator).\n")
code, out, _ = run({"k": ("k", "Kay Example", "", quiet_urls)}, ["k"])
expect(code == 0 and out == [], "(k) stays quiet on a work email, a DOI and a wiki link inside URLs", "\n".join(out))
# Prose is not an address: a number, then lower-case words, then "St." or "Dr." (the fully case-insensitive
# pattern flagged all of these). A capital "I" before the next word is still not a street name.
prose = ("\n\nIn 2008 he moved to St. Louis.\nShe spent 4 years working with Dr. Chen.\n"
         "Since 2010 she taught at St Andrews.\nIn 2008 I moved to St. Louis.\n")
code, out, _ = run({"k": ("k", "Kay Example", "", prose)}, ["k"])
expect(code == 0 and out == [], "(k) stays quiet on prose with a number and St. or Dr.", "\n".join(out))
# (k) a line over 10000 characters fails instead of being scanned, one at the limit is scanned, and
# a 200k-character ordinary word (quadratic for the old email pattern) is answered at once.
for case, word, want_code in (("over the limit", "a" * 10_001, 1), ("at the limit", "a" * 10_000, 0), ("200k characters", "a" * 200_000, 1)):
    body = f"\n\n{word}\n"
    line = persona("k", "Kay Example", "", body).split("\n").index(word) + 1
    start = time.monotonic()
    code, out, _ = run({"k": ("k", "Kay Example", "", body)}, ["k"])
    expect(code == want_code and time.monotonic() - start < 10
           and out == ([f"{GTM}k.md: (k) private-detail: line {line} is over 10000 characters, not scanned"] if want_code else []),
           f"(k) a line {case} {'fails, unscanned' if want_code else 'is scanned and passes'}", "\n".join(out))

# 676: (b) names how many sources are not https:// and their item numbers, never the values.
with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
    board(Path(t), {"b": ("b", "Bee Example", "", "")})
    f = Path(t) / GTM / "b.md"
    f.write_text(f.read_text().replace("https://www.ascd.org/books/understanding-by-design-expanded-2nd-edition\n  - https://en",
                                       "http://example.org/zq7?q=zq7\n  - ftp://example.org/zq7\n  - https://en", 1))
    p = subprocess.run([sys.executable, "scripts/check-personas.py", GTM + "b.md"], cwd=t, capture_output=True, text=True)
expect(p.returncode == 1 and p.stdout.splitlines() == [f"{GTM}b.md: (b) sources: 2 not https:// (items 2, 3)"]
       and "zq7" not in p.stdout, "(b) names the count and item numbers of non-https sources, never their values", p.stdout + p.stderr)

# --all walks every persona file on the board.
code, out, err = run({"clean-example": CLEAN}, [], args=("--all",))
expect(code == 0 and err == "check-personas: 2/2 pass", "--all checks every board file", err)

# Input safety: a symlink is refused with a diagnostic and its target is never opened. The checker runs
# under an audit hook that kills the process if the sentinel (a fabricated file beside the fake board,
# or inside a fake outside folder) is opened at all; MARK must not reach the output either.
WATCH = ("import os, runpy, sys\n"
         "want = os.path.realpath(sys.argv[1])\n"
         "def hook(event, args):\n"
         "    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)) and os.path.realpath(args[0]) == want:\n"
         "        sys.stderr.write('SENTINEL OPENED\\n'); sys.stderr.flush(); os._exit(7)\n"
         "sys.addaudithook(hook)\n"
         "sys.argv = sys.argv[2:]\n"
         "runpy.run_path(sys.argv[0], run_name='__main__')\n")
MARK = "SENTINEL-MARKER-7f3a"
SD = "systems/superintelligence/"
CANT = "(a) frontmatter: cannot read file: "


def symlinked(what, links, args, want, sentinel="outside.md", content=None, unlink=()):
    """links: {path in the fake board: its target, relative to its folder}. want(code, stdout lines, stderr) -> bool."""
    with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
        tmp = Path(t)
        board(tmp, {"clean-example": CLEAN})
        (tmp / sentinel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / sentinel).write_text(content or persona("clean-example", "Clean Example", "", f"\n{MARK}\n"), encoding="utf-8")
        for path in unlink:
            (tmp / path).unlink()
        for path, target in links.items():
            (tmp / path).parent.mkdir(parents=True, exist_ok=True)
            (tmp / path).symlink_to(target)
        p = subprocess.run([sys.executable, "-c", WATCH, str(tmp / sentinel), "scripts/check-personas.py", *args],
                           cwd=tmp, capture_output=True, text=True)
        seen = p.stdout + p.stderr
        expect(p.returncode != 7 and "SENTINEL OPENED" not in seen and MARK not in seen and "Traceback" not in seen
               and want(p.returncode, p.stdout.splitlines(), p.stderr.strip()), what, f"exit {p.returncode}\n{seen}")


symlinked("a persona file that links to a file outside the board is refused, never opened",
          {GTM + "link.md": "../../../../outside.md"}, [GTM + "link.md"],
          lambda c, o, e: c == 1 and o == [f"{GTM}link.md: {CANT}outside its allowed folder"])
symlinked("a persona file that links to another file inside the board is refused too",
          {GTM + "alias.md": "clean-example.md"}, [GTM + "alias.md"],
          lambda c, o, e: c == 1 and o == [f"{GTM}alias.md: {CANT}a symlink"], sentinel="unused.md")
symlinked("a registry.json that links outside the board is refused, so (d) fires",
          {SD + "gtm/registry.json": "../../../outside.json"}, [GTM + "clean-example.md"],
          lambda c, o, e: c == 1 and o == [f"{GTM}clean-example.md: (d) roster: no readable registry.json or roster.json beside this personas/ folder"],
          sentinel="outside.json", content=json.dumps({"personas": {"clean-example": {"slug": "clean-example"}}, "note": MARK}),
          unlink=[SD + "gtm/registry.json"])
symlinked("an optout.sha256 that links outside the board is refused: exit 2, never opened",
          {"docs/personas/optout.sha256": "../../outside.txt"}, [GTM + "clean-example.md"],
          lambda c, o, e: c == 2 and e.endswith(": outside its allowed folder") and "cannot read" in e,
          sentinel="outside.txt", content=f"{sha('Clean Example')}\n{MARK}\n", unlink=["docs/personas/optout.sha256"])
# The sentinel has the same slug and name as clean-example.md: indexed as a duplicate, its resolved path
# (outside the board) used to raise from relative_to. Now it is skipped, so only the link itself fails.
symlinked("--all over a board holding a link to an identical outside persona: refused, no crash, no false duplicate",
          {GTM + "twin.md": "../../../../outside.md"}, ["--all"],
          lambda c, o, e: c == 1 and o == [f"{GTM}twin.md: {CANT}outside its allowed folder"] and e == "check-personas: 2/3 pass")
symlinked("--all over a department folder that links outside the board: refused file by file, nothing opened",
          {SD + "evil": "../../outside_dept"}, ["--all"],
          lambda c, o, e: c == 1 and len(o) == 1 and o[0].startswith(f"{SD}evil/personas/x.md: {CANT}"),
          sentinel="outside_dept/personas/x.md")

# Only a regular file of at most 1 MiB is read: a named pipe would block an open that waits for a writer, a
# huge file would be read whole. Both are refused with a diagnostic (the run is cut off after 20 s if one hangs).
with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
    tmp = Path(t)
    board(tmp, {"clean-example": CLEAN})
    os.mkfifo(tmp / GTM / "pipe.md")
    (tmp / GTM / "big.md").write_text("x" * ((1 << 20) + 1))
    for name, why in (("pipe", "not a regular file"), ("big", "larger than 1048576 bytes")):
        try:
            p = subprocess.run([sys.executable, "scripts/check-personas.py", GTM + name + ".md"],
                               cwd=tmp, capture_output=True, text=True, timeout=20)
            ok, seen = p.returncode == 1 and p.stdout.splitlines() == [f"{GTM}{name}.md: {CANT}{why}"], p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            ok, seen = False, "hung"
        expect(ok, f"a {name} file is refused: {why}", seen)
    # A file that is not UTF-8 is a clean "cannot read file" line, not a traceback.
    (tmp / GTM / "latin.md").write_bytes(b"---\nreal_name: Caf\xe9\n---\n")
    p = subprocess.run([sys.executable, "scripts/check-personas.py", GTM + "latin.md"], cwd=tmp, capture_output=True, text=True)
    expect(p.returncode == 1 and p.stdout.startswith(f"{GTM}latin.md: {CANT}") and "Traceback" not in p.stderr,
           "a file that is not UTF-8 is refused with a diagnostic, no traceback", p.stdout + p.stderr)

# --links, offline: resolution and fetching stubbed.
spec = importlib.util.spec_from_file_location("check_personas", CHECK)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def timed(fn, limit=10):
    """(result, seconds, finished): fn runs in a daemon thread, so a hang fails its case instead of the suite."""
    box = {}
    worker = threading.Thread(target=lambda: box.update(out=fn()), daemon=True)
    start = time.monotonic()
    worker.start()
    worker.join(limit)
    return box.get("out"), time.monotonic() - start, not worker.is_alive()


# Scanning is linear: 200k characters of one ordinary word, dots, blanks or stray '<' is a single pass. The old
# patterns retried from every offset (e.g. 20k characters of "a" took the email pattern over 5 s).
for case, text in (("an ordinary word", "a" * 200_000), ("dotted words", "a." * 100_000), ("blanks", " " * 200_000),
                   ("digits and blanks", "1 " * 100_000), ("quotes", "'" * 200_000), ("quotes and blanks", "' " * 100_000),
                   ("a number and capitalized words", "1 Ab " * 40_000), ("a number and single capitals", "1 A " * 70_000)):
    scan = lambda: ([rx.search(text) for _, rx in mod.PRIVATE], mod.URL_TEXT.sub(" ", text),
                    mod.scalar("x" + text + "x"), mod.scalar("'" + text), mod.scalar("'" + text + "' # c"))
    spent = min(timed(scan)[1] for _ in range(3))  # best of three: a busy machine must not fail a linear scan
    expect(spent < 1, f"(k) patterns and scalar() take {spent:.2f} s on 200k characters of {case} (< 1 s)")
# scalar(): quotes are no part of a quoted value, with or without a trailing comment; a '#' inside quotes is kept.
shapes = {'"Opted Out Person" # note': "Opted Out Person", "'Opted Out Person' # it's fine": "Opted Out Person",
          '"Opted Out Person"': "Opted Out Person", "Opted Out Person # note": "Opted Out Person",
          "'a # b' # c": "a # b", '"a # b"': "a # b", "  'x'   # c  ": "x", "''": "", "'": "'", "~": None, "x #": "x"}
bad = {k: mod.scalar(k) for k, v in shapes.items() if mod.scalar(k) != v}
expect(not bad, "scalar() drops the quotes of a quoted value, with or without a trailing comment", bad)

# 608(3): the size cap counts bytes, not characters. The file grows after the fstat (made here to report the
# size it had before), to just over MAX_FILE bytes of two-byte characters: well under MAX_FILE characters.
# A CRLF file still reads as "\n" lines, as it did when the file was opened in text mode.
with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
    grew, crlf = Path(t) / "grew.md", Path(t) / "crlf.md"
    grew.write_bytes(("é" * (mod.MAX_FILE // 2 + 1)).encode("utf-8"))
    crlf.write_bytes(b"---\r\nslug: x\r\n")
    real_fstat = os.fstat

    class BeforeGrowth:
        def __init__(self, fd):
            self.st_mode, self.st_size = real_fstat(fd).st_mode, 0

    os.fstat = BeforeGrowth
    try:
        try:
            mod.read_file(grew, roots=(t,))
            why = "read"
        except mod.Unsafe as e:
            why = str(e)
        text = mod.read_file(crlf, roots=(t,))
    finally:
        os.fstat = real_fstat
expect(why == f"larger than {mod.MAX_FILE} bytes" and text == "---\nslug: x\n",
       "a file over MAX_FILE bytes but under MAX_FILE characters is refused (a byte-counted read)",
       f"grew.md: {why}; crlf.md: {text!r}")


def links(fm):
    """link_problems with the whole frontmatter on line 1 of the file."""
    return mod.link_problems(fm, [json.dumps(fm)])


real_fetch = mod.fetch
try:
    for case, markup in (("stray '<'", "<" * 200_000), ("unclosed tags", "<a href=" * 25_000), ("one '<' and text", "<" + "x" * 200_000)):
        mod.fetch = lambda url: (200, "text/html", markup.encode())
        out, spent, _ = timed(lambda: links({"canonical_works": [{"title": "Real Title", "url": "https://ok.example/page"}]}))
        expect(spent < 1 and out == ["(links) ok.example, line 1: title not found on the page"],
               f"--links reads a 200k-character page of {case} in {spent:.2f} s (< 1 s)", out)
finally:
    mod.fetch = real_fetch

DNS = {"ok.example": ["93.184.216.34"], "loop.example": ["127.0.0.1"], "ten.example": ["10.0.0.5"],
       "mixed.example": ["93.184.216.34", "10.0.0.5"], "meta.example": ["169.254.169.254"], "v6.example": ["::1"]}
ROUTES = {"/page": (200, {"Content-Type": "text/html"}, b"<html><title>The Real Title</title></html>"),
          "/to-http": (301, {"Location": "http://ok.example/page"}, b""),
          "/to-meta": (302, {"Location": "https://meta.example/page"}, b""),
          "/to-v6": (307, {"Location": "https://v6.example/page"}, b"")}
for chain, hops in (("a", 5), ("b", 6)):
    for i in range(hops):
        ROUTES[f"/{chain}{i}"] = (308, {"Location": f"/{chain}{i + 1}"}, b"")
ROUTES["/a5"] = ROUTES["/page"]
lookups, connects = [], []


def fake_getaddrinfo(host, port, *a, **k):
    lookups.append(host)
    if host not in DNS:
        raise socket.gaierror(f"unknown host {host}")
    return [(socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port)) for ip in DNS[host]]


class FakeResponse:
    def __init__(self, status, headers, body):
        self.status, self.headers, self.body = status, headers, body

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def read(self, n=-1):
        return self.body[:n]

    def read1(self, n=-1):  # one chunk per call, empty once the body is used up (the checker reads a chunk at a time)
        chunk, self.body = (self.body, b"") if n < 0 else (self.body[:n], self.body[n:])
        return chunk


class FakeConnection:
    def __init__(self, host, port, address):
        self.host, self.address = host, address

    def connect(self):
        pass

    def request(self, method, path, headers=None):
        connects.append((self.host, self.address, path))
        self.path = path

    def getresponse(self):
        return FakeResponse(*ROUTES[self.path])

    def close(self):
        pass


def no_network(*a, **k):
    raise AssertionError("real network used")


real = (socket.getaddrinfo, socket.create_connection, socket.socket.connect, mod.PinnedHTTPS)
socket.getaddrinfo, socket.create_connection, socket.socket.connect = fake_getaddrinfo, no_network, no_network
mod.PinnedHTTPS = FakeConnection
try:
    # (case, url, the only requests allowed: the safe hops before the refusal)
    for case, url, sent in (
        ("an http:// link", "http://ok.example/page", []),
        ("a host resolving to 127.0.0.1", "https://loop.example/page", []),
        ("a host resolving to 10.0.0.5", "https://ten.example/page", []),
        ("a host with one public and one private address", "https://mixed.example/page", []),
        ("a redirect to http://", "https://ok.example/to-http", ["ok.example/to-http"]),
        ("a redirect to a host resolving to 169.254.169.254", "https://ok.example/to-meta", ["ok.example/to-meta"]),
        ("a redirect to a host resolving to ::1", "https://ok.example/to-v6", ["ok.example/to-v6"]),
        ("a 6th redirect", "https://ok.example/b0", [f"ok.example/b{i}" for i in range(6)]),
    ):
        lookups.clear(), connects.clear()
        out = links({"sources": [url]})
        fetched = [host + path for host, _, path in connects]
        expect(len(out) == 1 and out[0].startswith(f"(links) {url.split('/')[2]}, line 1: refused: ") and fetched == sent,
               f"--links refuses {case}, never fetching it", "\n".join(out) + f"\nfetched: {fetched}")
    lookups.clear(), connects.clear()
    out = links({"sources": ["https://ok.example/a0"],
                             "canonical_works": [{"title": "The Real Title", "url": "https://ok.example/a0"}]})
    pinned = all(addr == DNS[host][0] for host, addr, _ in connects)
    expect(out == [] and len(connects) == 6 and lookups == ["ok.example"] * 6 and pinned,
           "--links follows 5 redirects, resolves once per hop and connects to the checked address",
           f"{out} {connects} {lookups}")
    out = links({"canonical_works": [{"title": "Another Title", "url": "https://ok.example/page"}]})
    expect(out == ["(links) ok.example, line 1: title not found on the page"],
           "--links reports a canonical_works title missing from its page", out)

    # One deadline per hop covers lookup, headers and body together: a hop that stalls, or answers a byte
    # at a time (each read inside the socket timeout), fails at it. HOP_TIMEOUT is shrunk to 0.3 s here.
    # Parked workers are released at the end and then fail, so none can reach a real socket.
    release = threading.Event()

    def stuck_lookup(host, port, *a, **k):
        release.wait()
        raise socket.gaierror("released")

    reads = []

    class DribbleResponse(FakeResponse):
        def read1(self, n=-1):
            reads.append(1)
            time.sleep(0.05)
            return b"x"

    class DribbleConnection(FakeConnection):
        silent = False

        def getresponse(self):
            if self.silent:
                release.wait()
                raise OSError("released")
            return DribbleResponse(200, {"Content-Type": "text/html"}, b"")

    class SilentConnection(DribbleConnection):
        silent = True

    workers = []

    def late_lookup(host, port, *a, **k):  # answers, but only after the hop has been given up on
        workers.append(threading.current_thread())
        release.wait()
        return fake_getaddrinfo(host, port)

    mod.HOP_TIMEOUT = 0.3
    try:
        for case, lookup, conn in (("a resolver that never returns", stuck_lookup, FakeConnection),
                                   ("a server that accepts and never sends headers", fake_getaddrinfo, SilentConnection),
                                   ("a body that arrives one byte at a time", fake_getaddrinfo, DribbleConnection),
                                   ("a resolver that answers after the deadline", late_lookup, FakeConnection)):
            socket.getaddrinfo, mod.PinnedHTTPS = lookup, conn
            connects.clear()
            out, spent, done = timed(lambda: links({"sources": ["https://ok.example/page"]}))
            expect(done and spent < 5 and out == ["(links) ok.example, line 1: dead: TimeoutError"],
                   f"--links gives up on {case} at the hop deadline", f"{out} after {spent:.1f} s, finished: {done}")
            if conn is DribbleConnection:  # the abandoned reader ends at the deadline too: no read starts after it
                time.sleep(0.2)
                seen = len(reads)
                time.sleep(0.2)
                expect(len(reads) == seen, "--links: the body reader of an abandoned hop stops at the deadline",
                       f"{seen} -> {len(reads)} reads")
        # The late lookup now returns a good answer: its abandoned worker must stop there, not dial.
        release.set()
        workers[0].join(5)
        expect(not workers[0].is_alive() and connects == [],
               "--links: a hop abandoned at its deadline does not dial when its lookup finally answers", connects)
    finally:
        mod.HOP_TIMEOUT = 30
        release.set()
        socket.getaddrinfo, mod.PinnedHTTPS = fake_getaddrinfo, FakeConnection

    # 608(2): a hop given up on at its deadline has its connection closed, so a read blocked on it ends
    # and its worker thread with it. The "server" is one end of a local socketpair that never writes.
    blocked = []

    class BlockedConnection(FakeConnection):
        def request(self, method, path, headers=None):
            self.sock, self.peer = socket.socketpair()
            blocked.append(self)

        def getresponse(self):
            self.worker = threading.current_thread()
            self.sock.recv(1)  # blocks until the socket is shut down
            raise OSError("read ended")

        def close(self):
            self.sock.close()

    mod.HOP_TIMEOUT, mod.PinnedHTTPS = 0.3, BlockedConnection
    try:
        try:
            mod.fetch("https://ok.example/page")
            timed_out = False
        except TimeoutError:
            timed_out = True
        conn = blocked[0]
        conn.worker.join(2)
        expect(timed_out and conn.sock.fileno() == -1 and not conn.worker.is_alive(),
               "--links closes the connection of a hop given up on at its deadline, so its blocked read ends",
               f"timed out: {timed_out}, socket open: {conn.sock.fileno() != -1}, worker alive: {conn.worker.is_alive()}")
    finally:
        mod.HOP_TIMEOUT, mod.PinnedHTTPS = 30, FakeConnection
        for c in blocked:
            c.peer.close()  # frees a worker the checker left blocked

    # 608(5c): a (links) line names the host, the line in the file and the reason: never the URL's path or
    # query, an exception's text or the title. Every path, query and title here carries the marker zq7.
    class InvalidConnection(FakeConnection):
        def request(self, method, path, headers=None):
            raise mod.http.client.InvalidURL(f"URL can't contain control characters. {path!r}")

    ROUTES["/gone-zq7?q=zq7"] = (404, {}, b"")
    ROUTES["/to-http-zq7?q=zq7"] = (301, {"Location": "http://ok.example/page-zq7?q=zq7"}, b"")
    fm = {"sources": ["http://ok.example/plain-zq7?q=zq7", "https://ok.example/gone-zq7?q=zq7",
                      "https://ok.example/to-http-zq7?q=zq7", "https://nohost.example/x-zq7?q=zq7",
                      "https://ok.example:99999/port-zq7?q=zq7"],
          "canonical_works": [{"title": "Missing Title zq7", "url": "https://ok.example/page"}]}
    lines = ["sources:", *fm["sources"], "canonical_works:", "https://ok.example/page"]
    out = mod.link_problems(fm, lines)
    mod.PinnedHTTPS = InvalidConnection
    out += mod.link_problems({"sources": ["https://ok.example/bad-zq7?q=zq7"]}, ["https://ok.example/bad-zq7?q=zq7"])
    mod.PinnedHTTPS = FakeConnection
    want = ["(links) ok.example, line 2: refused: not https",
            "(links) ok.example, line 3: dead: HTTP 404",
            "(links) ok.example, line 4: refused: redirect to a non-https URL",
            "(links) nohost.example, line 5: refused: cannot resolve the host",
            "(links) ok.example, line 6: refused: bad port",
            "(links) ok.example, line 8: title not found on the page",
            "(links) ok.example, line 1: dead: InvalidURL"]
    expect(out == want and not any("zq7" in l for l in out),
           "--links diagnostics show only the host, the line and the reason (no path, query, error text or title)",
           "\n".join(out))

    # 676: the contact policy runs before every hop: a redirect whose target carries a phone number is refused
    # with a fixed reason, and the second hop is never made. Invented number on an example host.
    ROUTES["/to-phone"] = (302, {"Location": "/card?tel=415-555-0134"}, b"")
    ROUTES["/card?tel=415-555-0134"] = ROUTES["/page"]
    connects.clear()
    out = links({"sources": ["https://ok.example/to-phone"]})
    fetched = [host + path for host, _, path in connects]
    expect(out == ["(links) ok.example, line 1: refused: contact detail in a redirect target"] and fetched == ["ok.example/to-phone"],
           "--links refuses a redirect to a URL carrying a phone number, never making the second hop",
           "\n".join(out) + f"\nfetched: {fetched}")

    # 676: resolver refusals are fixed categories, never the resolver's text or the address.
    DNS["zq7.example"] = ["10.9.9.7"]
    out = [links({"sources": [u]})[0] for u in ("https://zq7.example/x", "https://unknown-zq8.example/x")]
    expect(out == ["(links) zq7.example, line 1: refused: the host resolves to a non-public address",
                   "(links) unknown-zq8.example, line 1: refused: cannot resolve the host"],
           "--links resolver refusals are fixed categories (no address, no resolver text)", "\n".join(out))
finally:
    socket.getaddrinfo, socket.create_connection, socket.socket.connect, mod.PinnedHTTPS = real

# The real connection class dials the checked address, never the host name.
dialed = []


def record(address, *a, **k):
    dialed.append(address)
    raise ConnectionRefusedError("stubbed")


socket.getaddrinfo, socket.create_connection = no_network, record
try:
    with contextlib.suppress(ConnectionRefusedError):
        mod.PinnedHTTPS("ok.example", 443, "93.184.216.34").connect()
finally:
    socket.getaddrinfo, socket.create_connection = real[0], real[1]
expect(dialed == [("93.184.216.34", 443)], "PinnedHTTPS connects to the checked address with no second lookup", dialed)

# Success path: the handshake names the original host (the certificate is checked against it, not against the
# address), the context verifies certificates and host names, and the dial still goes to the checked address.
named = []


handshakes = []


class NameRecorder:  # returns a new socket object, as TLS wrapping does
    def wrap_socket(self, sock, server_hostname=None, do_handshake_on_connect=True):
        named.append(server_hostname)
        tls = FakeSock()
        if do_handshake_on_connect:
            tls.do_handshake()
        return tls


class FakeSock:
    def settimeout(self, seconds):
        pass

    def close(self):
        pass

    def do_handshake(self):  # records whether hang_up could reach this socket while the handshake runs
        handshakes.append(getattr(conn, "transport", None) is self)


dialed.clear()
socket.getaddrinfo = no_network
socket.create_connection = lambda address, *a, **k: dialed.append(address) or FakeSock()
try:
    conn = mod.PinnedHTTPS("ok.example", 443, "93.184.216.34")
    verifying = conn.tls.verify_mode == ssl.CERT_REQUIRED and conn.tls.check_hostname
    conn.tls = NameRecorder()
    conn.connect()
finally:
    socket.getaddrinfo, socket.create_connection = real[0], real[1]
expect(verifying and named == ["ok.example"] and handshakes == [True] and dialed == [("93.184.216.34", 443)],
       "PinnedHTTPS verifies certificates, names the original host in the handshake and dials the checked address"
       " (the TLS socket is on the connection before its handshake starts)",
       f"verifying={verifying} named={named} handshakes={handshakes} dialed={dialed}")

# 608(2) race: a connection hang_up closed before it connected must not reconnect on its own. http.client's
# default auto_open would quietly call connect() again from request(), opening a connection nobody watches.
calls = []


class CountingHTTPS(mod.PinnedHTTPS):
    def connect(self):
        calls.append(1)
        raise AssertionError("connect() called again")


conn = CountingHTTPS("ok.example", 443, "93.184.216.34")
mod.hang_up(conn)
try:
    conn.request("GET", "/page")
    raised = "nothing"
except Exception as e:
    raised = e.__class__.__name__
expect(raised == "NotConnected" and calls == [],
       "a connection hang_up closed before it connected raises NotConnected on request(), never reconnecting",
       f"raised {raised}, connect() calls: {len(calls)}")

# 676: hang_up reaches the socket that owns the descriptor in every phase after the lookup. The "server" is
# one end of a local socketpair; the dial is stubbed to return the other end. Each case's worker must end
# within 5 s of hang_up (the per-read socket timeout is 10 s, so a hang_up that misses fails the case).


def cancelled(phase, connect_tls, server):
    """Run conn.connect() (and, for the body, a GET) in a worker; server(peer, ready) plays the server and
    sets ready once the worker is blocked in the phase under test; then hang_up and time the worker."""
    a, b = socket.socketpair()
    conn = mod.PinnedHTTPS("ok.example", 443, "93.184.216.34")
    if connect_tls:
        conn.tls = connect_tls
    ready, seen = threading.Event(), {}

    def work():
        try:
            conn.connect()
            conn.request("GET", "/page")
            resp = conn.getresponse()
            seen["sock cleared"] = conn.sock is None
            seen["first"] = resp.read1(5)
            ready.set()
            resp.read1(5)  # blocks: the server sends no more
        except Exception as e:  # how the worker ended, for the failure detail
            seen["ended by"] = e.__class__.__name__

    socket.getaddrinfo, socket.create_connection = no_network, lambda *x, **k: a
    try:
        worker = threading.Thread(target=work, daemon=True)
        worker.start()
        server(b, ready)
        ok_ready = ready.wait(5)
        mod.hang_up(conn)
        worker.join(5)
        alive = worker.is_alive()
    finally:
        socket.getaddrinfo, socket.create_connection = real[0], real[1]
        b.close()  # frees a worker the checker left blocked
    expect(ok_ready and not alive, f"hang_up ends {phase}", f"ready: {ok_ready}, worker alive: {alive}, seen: {seen}")
    return seen


def in_handshake(peer, ready):
    peer.settimeout(5)
    with contextlib.suppress(OSError):
        peer.recv(1)  # the ClientHello: the worker is now waiting inside the TLS handshake
    ready.set()


cancelled("a TLS handshake that gets no answer", None, in_handshake)


class PlainTLS(socket.socket):  # stands in for SSLSocket: takes the descriptor over from the raw socket
    def do_handshake(self):
        pass


class NoTLS:
    def wrap_socket(self, sock, server_hostname=None, do_handshake_on_connect=True):
        timeout = sock.gettimeout()  # as SSLSocket does: a socket built on a non-blocking descriptor starts non-blocking
        tls = PlainTLS(sock.family, sock.type, fileno=sock.detach())
        tls.settimeout(timeout)
        if do_handshake_on_connect:
            tls.do_handshake()
        return tls


def mid_body(peer, ready):  # answers with "Connection: close" (so getresponse clears conn.sock), then stalls
    peer.settimeout(5)
    with contextlib.suppress(OSError):
        peer.recv(65536)
        peer.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\nhello")


# hang_up during the TCP dial has no socket to shut down: the dial may finish, but no handshake starts.
wraps = []


class CountingTLS:
    def wrap_socket(self, sock, **k):
        wraps.append(1)
        raise AssertionError("handshake started")


a, b = socket.socketpair()
conn = mod.PinnedHTTPS("ok.example", 443, "93.184.216.34")
conn.tls = CountingTLS()
socket.getaddrinfo, socket.create_connection = no_network, lambda *x, **k: mod.hang_up(conn) or a
try:
    conn.connect()
    raised = "nothing"
except Exception as e:
    raised = e.__class__.__name__
finally:
    socket.getaddrinfo, socket.create_connection = real[0], real[1]
    a.close(), b.close()
expect(raised == "TimeoutError" and wraps == [], "hang_up during the TCP dial: the dial finishes, but no TLS handshake starts",
       f"raised {raised}, handshakes started: {len(wraps)}")

# hang_up inside wrap_socket: the raw socket is already detached (so its shutdown reaches nothing) and the TLS
# socket is not yet on the connection. The flag must still stop the handshake.
handshook = []


class HandshakeRecorder(PlainTLS):
    def do_handshake(self):
        handshook.append(1)


class HangUpInWrap:
    def wrap_socket(self, sock, server_hostname=None, do_handshake_on_connect=True):
        tls = HandshakeRecorder(sock.family, sock.type, fileno=sock.detach())
        mod.hang_up(conn)  # conn.transport is still the detached raw socket here
        return tls


a, b = socket.socketpair()
conn = mod.PinnedHTTPS("ok.example", 443, "93.184.216.34")
conn.tls = HangUpInWrap()
socket.getaddrinfo, socket.create_connection = no_network, lambda *x, **k: a
try:
    conn.connect()
    raised = "nothing"
except Exception as e:
    raised = e.__class__.__name__
finally:
    socket.getaddrinfo, socket.create_connection = real[0], real[1]
    b.close()
expect(raised == "TimeoutError" and handshook == [], "hang_up inside wrap_socket (raw socket detached): no TLS handshake starts",
       f"raised {raised}, handshakes: {len(handshook)}")

seen = cancelled("a body read after getresponse has cleared conn.sock", NoTLS(), mid_body)
expect(seen.get("sock cleared") is True and seen.get("first") == b"hello",
       "the body case really reads after getresponse cleared conn.sock", seen)

# End to end: --links output lines carry the file name and the refusal.
with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
    board(Path(t), {"clean-example": CLEAN})
    f = Path(t) / GTM / "clean-example.md"
    f.write_text(f.read_text().replace("https://en.wikipedia.org/wiki/Grant_Wiggins", "http://ok.example/page"))
    spec = importlib.util.spec_from_file_location("check_personas_tmp", Path(t) / "scripts/check-personas.py")
    tmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tmod)
    tmod.link_problems = lambda fm, *lines: [f"(links) {u}: refused: stubbed" for u in fm["sources"] if u.startswith("http:")]
    buf, ebuf = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(ebuf):
        code = tmod.main(["--links", str(f)])
    lines = buf.getvalue().splitlines()
    expect(code == 1 and any(l.endswith(": (links) http://ok.example/page: refused: stubbed") for l in lines),
           "--links problems print as <file>: (links) <url>: refused: <reason>", buf.getvalue() + ebuf.getvalue())

# --all over the real board makes no network call. boom exits the process at
# once, so no handler in the checker can swallow a network call and still pass.
guard = ("import os, socket, runpy, sys\n"
         "def boom(*a, **k): sys.stderr.write('network used\\n'); sys.stderr.flush(); os._exit(3)\n"
         "socket.socket.connect = socket.socket.connect_ex = boom\n"
         "socket.create_connection = socket.getaddrinfo = socket.gethostbyname = boom\n"
         "sys.argv = [sys.argv[1], *sys.argv[2:]]\n"
         "runpy.run_path(sys.argv[0], run_name='__main__')\n")
p = subprocess.run([sys.executable, "-c", guard, str(CHECK), "--all"], cwd=ROOT, capture_output=True, text=True)
n = len(list((ROOT / "systems/superintelligence").glob("*/personas/*.md")))
summary = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ""
expect(p.returncode in (0, 1) and re.fullmatch(rf"check-personas: \d+/{n} pass", summary)
       and "Traceback" not in p.stderr and "network used" not in p.stderr,
       f"--all over the real board runs offline with sockets made to raise ({summary})", p.stderr[-2000:])
# The guard itself works: --links does reach for the network and is stopped.
p = subprocess.run([sys.executable, "-c", guard, str(CHECK), "--links", str(GOOD)], cwd=ROOT, capture_output=True, text=True)
expect(p.returncode == 3 and "network used" in p.stderr, "the no-network guard stops a --links run", p.stderr[-500:])

# A file with a (k) finding is not fetched under --links: a URL that carries a private detail goes nowhere.
# Same guard as above, so any attempt to resolve or connect ends the run with exit 3.
with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
    tmp = Path(t)
    board(tmp, {"k": ("k", "Kay Example", "", "")})
    f = tmp / GTM / "k.md"
    f.write_text(f.read_text().replace("https://en.wikipedia.org/wiki/Grant_Wiggins", "https://example.com/p?email=jane.doe%40gmail.com"))
    n = next(i for i, l in enumerate(f.read_text().split("\n"), 1) if "jane.doe" in l)
    p = subprocess.run([sys.executable, "-c", guard, "scripts/check-personas.py", "--links", GTM + "k.md"],
                       cwd=tmp, capture_output=True, text=True)
    expect(p.returncode == 1 and "network used" not in p.stderr
           and p.stdout.splitlines() == [f"{GTM}k.md: (k) private-detail: line {n} looks like a personal email address"],
           "--links does not fetch a file with a (k) finding", p.stdout + p.stderr)

# 608(5a): before --links fetches anything, the decoded path and query of every URL it would fetch are checked
# for a phone number, a personal email and a street address. A match is a (k) line and nothing is fetched (the
# fetch stub records every call). Invented people and numbers on example.org only. The last two are URLs the
# line scan cannot see whole: a quoted URL with literal spaces, and '+' for a space in the query.
results = {}
for case, url, what, secret in (
        ("a phone number in the query", "https://example.org/card?tel=415-555-0134", "a phone number", "0134"),
        ("a personal email in the query", "https://example.org/contact?to=jane.doe%40gmail.com", "a personal email address", "jane"),
        ("a street address in the path", "https://example.org/visit/221%20Baker%20Street", "a street address", "baker"),
        ("a street address in a quoted URL", '"https://example.org/visit/12 Elm Rd"', "a street address", "elm"),
        ("a street address in the query, '+' for space", "https://example.org/map?at=221+Baker+Street", "a street address", "baker")):
    with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
        board(Path(t), {"k": ("k", "Kay Example", "", "")})
        f = Path(t) / GTM / "k.md"
        f.write_text(f.read_text().replace("https://en.wikipedia.org/wiki/Grant_Wiggins", url))
        n = next(i for i, l in enumerate(f.read_text().split("\n"), 1) if url in l)
        spec = importlib.util.spec_from_file_location("check_personas_k", Path(t) / "scripts/check-personas.py")
        tmod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tmod)
        fetched = []
        tmod.fetch = lambda u: fetched.append(u) or (200, "text/html", b"")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = tmod.main(["--links", str(f)])
        lines = buf.getvalue().splitlines()
        ok = (code == 1 and not fetched and lines == [f"{f}: (k) private-detail: line {n} looks like {what}"]
              and secret not in buf.getvalue().replace(str(f), "").lower())
        results[case] = "ok" if ok else f"exit {code}, fetched {len(fetched)}, output {lines}"
expect(all(v == "ok" for v in results.values()),
       "--links checks each URL's path and query for a phone, a personal email and a street address before any fetch",
       "\n".join(f"{k}: {v}" for k, v in results.items()))

print("check-personas-rules-test:", "all passed" if not failures else f"{failures} case(s) failed")
sys.exit(1 if failures else 0)
