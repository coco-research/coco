#!/usr/bin/env python3
"""Planted cases for scripts/check-personas.py rules (e), (i), (j), (k), --all and --links.

Everything here is offline:
- each case builds a small board in a temp folder (a copy of the checker, the
  label template, a strategy and a gtm department) and plants one problem;
- --links runs with name resolution and fetching stubbed, never the network;
- --all runs over the real board with socket connections made to raise.

Run from repo root: python3 tests/check-personas-rules-test.py
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
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

# --all walks every persona file on the board.
code, out, err = run({"clean-example": CLEAN}, [], args=("--all",))
expect(code == 0 and err == "check-personas: 2/2 pass", "--all checks every board file", err)

# --links, offline: resolution and fetching stubbed.
spec = importlib.util.spec_from_file_location("check_personas", CHECK)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

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


class FakeConnection:
    def __init__(self, host, port, address):
        self.host, self.address = host, address

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
        out = mod.link_problems({"sources": [url]})
        fetched = [host + path for host, _, path in connects]
        expect(len(out) == 1 and out[0].startswith(f"(links) {url}: refused: ") and fetched == sent,
               f"--links refuses {case}, never fetching it", "\n".join(out) + f"\nfetched: {fetched}")
    lookups.clear(), connects.clear()
    out = mod.link_problems({"sources": ["https://ok.example/a0"],
                             "canonical_works": [{"title": "The Real Title", "url": "https://ok.example/a0"}]})
    pinned = all(addr == DNS[host][0] for host, addr, _ in connects)
    expect(out == [] and len(connects) == 6 and lookups == ["ok.example"] * 6 and pinned,
           "--links follows 5 redirects, resolves once per hop and connects to the checked address",
           f"{out} {connects} {lookups}")
    out = mod.link_problems({"canonical_works": [{"title": "Another Title", "url": "https://ok.example/page"}]})
    expect(out == ["(links) https://ok.example/page: title not found on the page: Another Title"],
           "--links reports a canonical_works title missing from its page", out)
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

# End to end: --links output lines carry the file name and the refusal.
with tempfile.TemporaryDirectory(prefix="check-personas-") as t:
    board(Path(t), {"clean-example": CLEAN})
    f = Path(t) / GTM / "clean-example.md"
    f.write_text(f.read_text().replace("https://en.wikipedia.org/wiki/Grant_Wiggins", "http://ok.example/page"))
    spec = importlib.util.spec_from_file_location("check_personas_tmp", Path(t) / "scripts/check-personas.py")
    tmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tmod)
    tmod.link_problems = lambda fm: [f"(links) {u}: refused: stubbed" for u in fm["sources"] if u.startswith("http:")]
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

print("check-personas-rules-test:", "all passed" if not failures else f"{failures} case(s) failed")
sys.exit(1 if failures else 0)
