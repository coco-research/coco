#!/usr/bin/env python3
"""Checker for Super Intelligence persona files (stdlib only; offline unless --links).

Usage:
  python3 scripts/check-personas.py [--all] [--links] [<persona.md> ...]

  --all     check every systems/superintelligence/*/personas/*.md file
  --links   also fetch each source, canonical_works, signal and stance URL (network, opt-in)

Prints one line per problem on stdout, "<file>: (<rule>) <name>: <detail>", warnings on
stderr, and exits 1 if there is any problem, 0 if every file passes, 2 on a setup error.

Rules (taken from the existing validate_persona.py / validate_offline.py copies,
templates/attribution.md and the real persona files):
  (a) frontmatter   parses, and has every field all shipped personas carry, non-empty;
                    real_name is one text value (a list or mapping would dodge (j))
  (b) sources       at least 3 sources, each an https:// URL (a failure names the item
                    numbers, never the values)
  (c) label         a file that speaks in the person's voice (a `> "..."` block)
                    carries the approved label line from templates/attribution.md
  (d) roster        the slug is listed in its department's registry.json / roster.json
  (e) quote         every `> "..."` line has an https:// URL, [paraphrase] or
                    [extrapolated] on the same or the next line
  (f) stances       every public_stances entry has an evidence_url
  (g) signals       active: >= 2 recent_signal_12mo; archetype: >= 2 persistent_signals;
                    every signal or persistent signal carries a non-empty title; a signal
                    whose title and takeaway lack any folded surname token from real_name
                    or aliases warns on stderr
  (h) pairs         pairs_well_with / productive_conflict_with name slugs listed in
                    some department's roster, or of a status: held file beside them
  (held)            status: held keeps a file out of the registry until it can be
                    sourced: it is exempt from (a) for signature_moves, canonical_works
                    and public_stances, and from (b), (d) and (g) count; every other rule holds
  (i) duplicate     slug, real_name and aliases (case-folded) are not used by any
                    other persona file on the board, in any department (except the
                    grandfathered two-team seats in TWO_TEAM_SEATS)
  (j) opted-out     the sha256 of the case-folded, space-collapsed real_name is not
                    in docs/personas/optout.sha256. A missing file is an empty
                    list, a comment-only file is an explicit empty list, and a
                    malformed row stops the run (exit 2) naming its line number,
                    never its text.
  (k) private-detail  no line looks like a phone number, a street address (a number,
                    Capitalized or ALL CAPS name words, then St, Ave, Rd, ... in any
                    case) or a personal (non-work) email address; the decoded text of
                    every URL is also scanned for all three; a line over 10000
                    characters fails instead of being skipped
  (links)           with --links: each source, canonical_works, signal, persistent-signal
                    and public_stances evidence_url answers 200 over https (HTTP 403 and
                    429 warn on stderr; 404, 410, DNS failure and refusals fail), and each
                    canonical_works title appears on its HTML page; a file with a (k)
                    finding is not fetched until that is fixed, and before anything is
                    fetched the decoded path and query of every URL to fetch get the same
                    three checks (a match is a (k) line)

Input safety: a persona, registry, roster, template or opt-out file is read only
if it is a regular file of at most 1 MiB (counted in bytes) inside the board (or
the test fixtures) and is not reached through a symlink; anything else prints a
"cannot read file" diagnostic. The threat model is the repo's own checked-out
tree as it stands: the checks are made on the path and then on the opened file,
so a path component swapped for a symlink while the checker runs is out of scope.
Every scanning pattern runs in time linear in the line. No message prints text
that matched a private-detail or opt-out check.

--links fetch safety: https only, on the first URL and every redirect hop; every
address each host resolves to must be public (stdlib ipaddress), and the
connection goes to the address that was checked, with no second lookup; the
(k) checks run on the decoded path and query of every hop's URL, redirect targets
included, before that hop is made; a per-operation timeout plus a deadline: 10 s
for the connect and for each read, and a 30 s deadline per hop. The deadline
always holds for the caller. When it passes, the socket that carries the hop is
shut down, which ends the TLS handshake, the headers or the body read, whichever
is running (the worker then closes it). Two phases have no socket to shut down
yet: a name lookup is left to finish, and a TCP connect runs out on its own 10 s
timeout; neither is then allowed to go on. At most 5
redirects, 2 MB read per page. A refused link prints "(links) <host>, line <n>:
refused: <reason>" and is never fetched; every reason is a fixed category, and no
(links) line prints a URL's path or query, a title, an address or an error's text.
"""
from __future__ import annotations

import contextlib
import hashlib
import html
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import stat
import sys
import threading
import time
import unicodedata
from pathlib import Path
from urllib.parse import unquote, unquote_plus, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "systems" / "superintelligence"
FIXTURES = ROOT / "tests" / "fixtures" / "personas"  # the only other folder persona files may live in
ATTRIBUTION = BOARD / "templates" / "attribution.md"
OPTOUT = ROOT / "docs" / "personas" / "optout.sha256"

CONNECT_TIMEOUT = READ_TIMEOUT = 10  # seconds
HOP_TIMEOUT = 30  # seconds: the deadline per hop, on top of the per-operation socket timeouts
MAX_REDIRECTS = 5
MAX_BYTES = 2 * 1024 * 1024
MAX_FILE = 1 << 20  # bytes: the most a persona, registry or opt-out file may hold (shipped max: 124 KB)
MAX_LINE = 10_000  # characters: (k) fails a longer line instead of scanning it (shipped max: 2,329)
REDIRECTS = (301, 302, 303, 307, 308)

# (k) ponytail: regex only; the second read catches what these miss. A PII
# library is the upgrade if second reads keep finding misses. Every pattern is
# linear in the line: no unbounded repeat that is retried from each offset, so a
# long word, blank run or dotted run costs one pass. A 33-character URL scheme
# is not recognised as a URL, so its text is scanned as plain text (the safe side).
URL_TEXT = re.compile(r"\b[a-z][a-z0-9+.-]{0,31}://\S+|\bwww\.\S+", re.I)
PRIVATE = [  # (what, pattern); each is also looked for in the decoded text of every URL
    ("a phone number", re.compile(
        r"(?<![\w.+/-])(?:\+\d{1,3}[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]\d{3}[ .-]\d{4}(?![\w-])"
        r"|(?<![\w.+/-])\+\d{1,3}(?:[ .-]\d{2,4}){2,4}(?![\w-])")),
    # Name words are Capitalized or ALL CAPS; only the street word ignores case ("In 2008 he moved to St. Louis" stays quiet).
    ("a street address", re.compile(
        r"\b\d{1,5}(?:\s+(?:[A-Z][a-z]+|[A-Z]+)){1,3}\s+"
        r"(?i:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct|terrace|parkway)\b")),
    ("a personal email address", re.compile(  # one local-part character is enough to tell it is an address
        r"[\w.+-]@(?:gmail|googlemail|yahoo|ymail|hotmail|outlook|live|msn|aol|icloud|me|mac"
        r"|proton|protonmail|pm|gmx|mail|yandex|zoho|qq|163|126|fastmail|hey)\.[a-z.]{2,6}\b", re.I)),
]

# The fields every one of the 495 shipped personas has, non-empty.
REQUIRED = ["slug", "real_name", "archetype", "teams", "cell", "cell_role", "status",
            "domains", "signature_moves", "canonical_works", "public_stances",
            "voice_style", "confidence", "sources"]
HELD_MAY_EMPTY = {"signature_moves", "canonical_works", "public_stances"}  # a held file may have emptied these

KEY = re.compile(r"^([A-Za-z0-9_]+):(?:\s+(.*))?$")
SUBKEY = re.compile(r"^\s*([A-Za-z0-9_]+):(?:\s+(.*))?$")
QUOTE = re.compile(r'^\s*>\s*["“]')
SOURCED = re.compile(r"https://|\[paraphrase\]|\[extrapolated\]")

# (i) ponytail: grandfathered two-team seats, one file per department, same slug.
# New people get one file with `teams:` instead; never add to this list.
TWO_TEAM_SEATS = frozenset({("demis-hassabis", "ai"), ("demis-hassabis", "healthcare-life-sciences"),
                            *((s, d) for s in ("ann-cavoukian", "daniel-solove", "frank-pasquale",
                                               "helen-nissenbaum", "lina-khan", "tim-wu")
                              for d in ("legal-ip", "risk-compliance"))})


def scalar(s: str):
    s = s.strip()
    q = re.fullmatch(r"""(['"])(.*?)\1(?:\s+#.*)?""", s)  # a quoted value, then maybe a comment: the quotes are no part of it
    if q:  # (a name left in its quotes would hash differently from the opt-out list, so (j) would miss it)
        return q.group(2)
    m = re.search(r"\s#", s)  # a trailing comment; one pass, not a blank-run pattern retried from each offset
    s = s[:m.start()].rstrip() if m else s
    return None if s in ("", "~", "null") else s


def flow_list(s: str) -> list:
    items = re.findall(r"'[^']*'|\"[^\"]*\"|[^,\[\]]+", s.strip()[1:-1])
    return [v for v in (scalar(i) for i in items) if v]


def parse_frontmatter(text: str):
    """Top-level keys of a persona frontmatter: scalars, lists of scalars, lists of maps.

    ponytail: covers the YAML shapes the persona files use, not full YAML.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    lines = text[4:end].split("\n")
    fm: dict = {}
    i = 0
    while i < len(lines):
        m = KEY.match(lines[i])
        i += 1
        if not m:
            continue
        key, rest = m.group(1), (m.group(2) or "").strip()
        block = []
        while i < len(lines) and (lines[i][:1] in (" ", "-") or not lines[i].strip()):
            block.append(lines[i])
            i += 1
        if rest.startswith("["):
            fm[key] = flow_list(rest[:rest.rfind("]") + 1])  # drop a trailing comment
        elif rest.startswith("{"):
            fm[key] = {} if rest.replace(" ", "") == "{}" else {"_": rest}
        elif rest and rest[0] not in "|>#":
            fm[key] = scalar(rest)
        elif rest[:1] in ("|", ">"):
            fm[key] = "\n".join(block).strip() or None
        else:
            fm[key] = block_value(block)
    return fm


def block_value(block: list):
    rows = [b for b in block if b.strip() and not b.strip().startswith("#")]
    if not rows:
        return None
    if not rows[0].lstrip().startswith("- "):
        return {"_": rows[0].strip()}  # a nested mapping: non-empty is all we need
    dash = len(rows[0]) - len(rows[0].lstrip())
    items: list = []
    for r in rows:
        ind = len(r) - len(r.lstrip())
        if ind == dash and r.lstrip().startswith("- "):
            body = r.lstrip()[2:]
            m = SUBKEY.match(body)
            items.append({m.group(1): scalar(m.group(2) or "")} if m and not body.startswith(("'", '"', "http")) else scalar(body))
        elif ind == dash + 2 and isinstance(items[-1], dict):
            m = SUBKEY.match(r)
            if m:
                items[-1][m.group(1)] = scalar(m.group(2) or "")
    return items


class Unsafe(OSError):
    """A file this checker will not read; the message says why."""


def read_file(p, roots=(BOARD, FIXTURES)) -> str:
    """Text of a regular file inside one of roots, reached without a symlink; else Unsafe.

    Every read goes through here. Threat model: the checker reads the repo's own
    checked-out tree. The path is resolved and every component below the root is
    checked for a symlink before the open; a component swapped while the checker
    runs (between those checks and the open) is out of scope. The open does not
    follow a symlink in the last component, the type and size checks are on the
    opened file, and at most MAX_FILE + 1 bytes are read before decoding.
    """
    lexical = Path(os.path.abspath(p))
    real = Path(os.path.realpath(lexical))
    top = next((r for r in map(os.path.realpath, roots) if Path(r) in real.parents), None)
    if top is None:
        raise Unsafe("outside its allowed folder")
    for q in (lexical, *lexical.parents):  # up to the root, which may itself sit behind a symlink (macOS /var)
        if os.path.realpath(q) == top:
            break
        if q.is_symlink():
            raise Unsafe("a symlink")
    # O_NONBLOCK: opening a named pipe must not wait for a writer; it is refused just below.
    fd = os.open(real, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(fd, "rb") as f:
        info = os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise Unsafe("not a regular file")
        if info.st_size > MAX_FILE:
            raise Unsafe(f"larger than {MAX_FILE} bytes")
        data = f.read(MAX_FILE + 1)  # bytes, capped here too: the file can grow after the fstat above
    if len(data) > MAX_FILE:
        raise Unsafe(f"larger than {MAX_FILE} bytes")
    # A decode error is a UnicodeDecodeError, which every caller reports as "cannot read". The newline
    # handling is what the old text-mode open did: CRLF and CR read as LF.
    return data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def roster_slugs(dept: Path, cache: dict):
    if dept not in cache:
        slugs, found = set(), False
        for name in ("registry.json", "roster.json"):
            p = dept / name
            if p.is_file():
                try:
                    data = json.loads(read_file(p))
                except (OSError, ValueError):
                    continue  # unreadable: counts as no roster, reported as (d)
                found = True
                people = data.get("personas") if isinstance(data, dict) else None
                if isinstance(people, (dict, list)):  # {slug: {...}} or [slug | {slug}]
                    slugs |= {s for s in people if isinstance(s, str)}
                stack = [data]
                while stack:
                    o = stack.pop()
                    if isinstance(o, dict):
                        if isinstance(o.get("slug"), str):
                            slugs.add(o["slug"])
                        stack.extend(o.values())
                    elif isinstance(o, list):
                        stack.extend(o)
        cache[dept] = slugs if found else None
    return cache[dept]


def label_template() -> str:
    try:
        m = re.search(r"\*\*<Name> persona\*\*: [^\n]*", read_file(ATTRIBUTION))
    except (OSError, UnicodeDecodeError) as e:
        m, why = None, f"cannot read: {e}"
    else:
        why = "approved label line not found"
    if not m:
        print(f"{ATTRIBUTION}: {why}", file=sys.stderr)
        sys.exit(2)  # setup error, distinct from exit 1 (files failed)
    return m.group(0).strip()


def norm(s) -> str:
    return " ".join(str(s).casefold().split())


NAME_SUFFIXES = frozenset({"jr", "sr", "ii", "iii", "iv", "v", "phd", "md"})
HYPHENS = re.compile(r"[-\u2010\u2011\u2013\u2014]")
WORD_TOK = re.compile(r"[^\W_]+")


def fold_name(s: str) -> str:
    """NFKD-fold (accents dropped), casefold, turn hyphens into spaces, collapse whitespace."""
    decomposed = unicodedata.normalize("NFKD", s)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(HYPHENS.sub(" ", stripped.casefold()).split())


def surname_tokens(fm: dict) -> set:
    """Folded surname tokens of real_name and aliases; initials (len <= 1) are ignored."""
    aliases = fm.get("aliases")
    aliases = aliases if isinstance(aliases, list) else ([aliases] if aliases is not None else [])
    tokens = set()
    for raw in (fm.get("real_name"), *aliases):
        if not isinstance(raw, str) or not raw.strip():
            continue
        cleaned = re.sub(r"\([^)]*\)", " ", raw).strip() or raw
        words = [w.strip(".,;:'\"") for w in cleaned.split()]
        words = [w for w in words if w]
        while len(words) > 1 and fold_name(words[-1]).replace(".", "") in NAME_SUFFIXES:
            words.pop()
        non_initial = [w for w in words if any(len(t) > 1 for t in WORD_TOK.findall(fold_name(w)))]
        if not non_initial:
            continue
        for tok in WORD_TOK.findall(fold_name(non_initial[-1])):
            if len(tok) > 1:
                tokens.add(tok)
    return tokens


def identity(fm: dict) -> set:
    aliases = fm.get("aliases")
    aliases = aliases if isinstance(aliases, list) else [aliases]
    keys = {("slug", norm(fm["slug"]))} if isinstance(fm.get("slug"), str) else set()
    return keys | {("name", norm(n)) for n in [fm.get("real_name"), *aliases] if isinstance(n, str) and n.strip()}


def board_identities(cache: dict) -> dict:
    """(kind, value) -> (persona file, its slug) for every board file that carries it."""
    if "identities" not in cache:
        index: dict = {}
        for p in sorted(BOARD.glob("*/personas/*.md")):
            try:
                fm = parse_frontmatter(read_file(p)) or {}
            except (OSError, UnicodeDecodeError):
                continue  # this file reports its own (a) when it is checked; a symlink is never indexed
            for key in identity(fm):
                index.setdefault(key, []).append((p.resolve(), fm.get("slug")))
        cache["identities"] = index
    return cache["identities"]


def held_slugs(board: Path, cache: dict) -> set:
    """Slugs of the status: held files in board's departments (the generators leave them out of the registry)."""
    if ("held", board) not in cache:
        held = set()
        for p in sorted(board.glob("*/personas/*.md")):
            try:
                fm = parse_frontmatter(read_file(p)) or {}
            except (OSError, UnicodeDecodeError):
                continue  # this file reports its own (a) when it is checked
            if fm.get("status") == "held" and isinstance(fm.get("slug"), str):
                held.add(fm["slug"])
        cache[("held", board)] = held
    return cache[("held", board)]


def load_optout() -> set:
    """Opt-out hashes. Missing file: empty list (the Step 2 gate is where its presence gets enforced).
    Empty or comment-only file: an explicit empty list. A row that is not a hash: exit 2."""
    try:
        text = read_file(OPTOUT, roots=(OPTOUT.parent,))
    except FileNotFoundError:
        return set()
    except (OSError, UnicodeDecodeError) as e:
        print(f"{OPTOUT}: cannot read: {e}", file=sys.stderr)
        sys.exit(2)
    rows = set()
    for n, raw in enumerate(text.splitlines(), 1):
        row = raw.strip().lower()
        if not row or row.startswith("#"):
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", row):  # a malformed line would silently match no one: fail closed
            print(f"{OPTOUT}: line {n} is not a sha256 hex line", file=sys.stderr)  # the row may be a plain name: never echo it
            sys.exit(2)
        rows.add(row)
    return rows


class Refused(Exception):
    """A link that the fetch-safety rules do not allow; it is never fetched."""


def is_public(ip) -> bool:
    embedded = [getattr(ip, "ipv4_mapped", None), getattr(ip, "sixtofour", None),
                *(getattr(ip, "teredo", None) or ())]
    if any(e is not None and not is_public(e) for e in embedded):
        return False
    return ip.is_global and not (ip.is_multicast or ip.is_private or ip.is_loopback or ip.is_link_local
                                 or ip.is_reserved or ip.is_unspecified)


def checked_address(host: str, port: int) -> str:
    """Resolve once; every address must be public. Returns the address to connect to."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (OSError, UnicodeError):
        raise Refused("cannot resolve the host")  # a fixed category: the resolver's text is not printed
    addrs = [ipaddress.ip_address(info[4][0].split("%")[0]) for info in infos]
    if not addrs:
        raise Refused("cannot resolve the host")
    if not all(is_public(a) for a in addrs):
        raise Refused("the host resolves to a non-public address")
    return str(addrs[0])


class PinnedHTTPS(http.client.HTTPSConnection):
    """HTTPS to an address already checked: no second lookup of the host name."""

    auto_open = 0  # a connection without a socket never redials: request() raises NotConnected instead
    hung_up = False  # set by hang_up; a dial that finishes after it goes no further

    def __init__(self, host: str, port: int, address: str):
        super().__init__(host, port, timeout=READ_TIMEOUT)
        self.address, self.tls = address, ssl.create_default_context()

    def connect(self):
        """Dial, then handshake. self.transport is always the socket that owns the descriptor (the raw one,
        then the TLS one before its handshake starts), and close() never clears it, so hang_up reaches it
        in the handshake and after getresponse has handed the connection to the response."""
        self.transport = socket.create_connection((self.address, self.port), timeout=CONNECT_TIMEOUT)
        try:
            if self.hung_up:  # hang_up came during the dial, when there was no socket to shut down
                raise TimeoutError("hung up during the connect")
            self.transport.settimeout(READ_TIMEOUT)
            self.transport = self.tls.wrap_socket(self.transport, server_hostname=self.host, do_handshake_on_connect=False)
            if self.hung_up:  # hang_up came inside the wrap, and its shutdown reached only the detached raw socket
                raise TimeoutError("hung up during the connect")
            self.transport.do_handshake()
        except BaseException:
            self.transport.close()
            raise
        self.sock = self.transport


def hang_up(conn) -> None:
    """Shut down conn's transport (else conn.sock) from another thread, so whatever I/O the worker
    is blocked in on it (TLS handshake, request, headers, body) fails at once.

    shutdown, not close: a response reader holds its own reference to the socket, so close() alone
    would leave the descriptor open and the read waiting, and closing from this thread races the
    worker (a TLS handshake blocked on it missed the wake-up in 1 of 3 local runs; shutdown alone
    never did). The worker closes the socket itself as its failed I/O unwinds: connect() on error,
    get_once's finally, or the response it was reading.
    """
    conn.hung_up = True  # set before the transport is read: connect() sets the transport, then reads this
    sock = getattr(conn, "transport", None) or getattr(conn, "sock", None)
    if sock is not None:
        with contextlib.suppress(OSError):
            sock.shutdown(socket.SHUT_RDWR)


def within(seconds: float, fn, *args, held: dict | None = None):
    """fn(*args) in a daemon thread; TimeoutError if it has not finished after `seconds`.

    The socket timeouts are per operation (the connect, each read), so a server that
    answers one byte at a time, or a resolver that never returns, would otherwise hold
    a hop for as long as it likes: this is the deadline on top of them, and it always
    holds for the caller. On timeout, held["expired"] is set and the connection fn put in
    held["conn"] is hung up, which ends its TLS handshake, header or body read, and the
    worker with it. ponytail: a worker still inside the name lookup or the TCP connect
    has no socket to shut down yet; it is abandoned (a daemon, so it never keeps the
    process alive), the connect gives up on its own 10 s timeout, and get_once does not
    let either go on.
    """
    box: dict = {}
    held = {} if held is None else held

    def run():
        try:
            box["ok"] = fn(*args)
        except BaseException as e:  # handed to the caller below
            box["err"] = e

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        held["expired"] = True
        if held.get("conn") is not None:
            hang_up(held["conn"])
        raise TimeoutError(f"no answer within {seconds:g} s")
    if "err" in box:
        raise box["err"]
    return box["ok"]


def check_time(deadline: float) -> None:
    if time.monotonic() > deadline:
        raise TimeoutError(f"no answer within {HOP_TIMEOUT:g} s")


def get_once(host: str, port: int, target: str, deadline: float, held: dict):
    """One GET to the checked address: (status, content type, Location or None, body).

    The connection goes in held["conn"], where within() hangs it up if the hop runs out of time.
    """
    address = checked_address(host, port)
    check_time(deadline)  # a lookup that stalled past the deadline must not go on to dial: within() has given up on this hop
    conn = PinnedHTTPS(host, port, address)
    held["conn"] = conn
    try:
        if held.get("expired"):  # within() gave up just before conn was stored, so it could not hang it up
            raise TimeoutError(f"no answer within {HOP_TIMEOUT:g} s")
        conn.connect()  # explicit: with auto_open off, request() never dials on its own
        if held.get("expired"):  # within() gave up during the connect
            raise TimeoutError(f"no answer within {HOP_TIMEOUT:g} s")
        conn.request("GET", target, headers={"User-Agent": "coco-check-personas", "Accept": "text/html,*/*"})
        resp = conn.getresponse()
        location = resp.getheader("Location")
        if resp.status in REDIRECTS and location:
            return resp.status, "", location, b""
        chunks, size = [], 0
        while size < MAX_BYTES:  # a chunk at a time, so the deadline is checked as the body arrives
            check_time(deadline)
            chunk = resp.read1(min(65536, MAX_BYTES - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        return resp.status, resp.getheader("Content-Type") or "", None, b"".join(chunks)
    finally:
        conn.close()


def fetch(url: str):
    """GET url under the fetch-safety rules. Returns (status, content_type, body)."""
    for hop in range(MAX_REDIRECTS + 1):
        parts = urlsplit(url)
        if parts.scheme != "https":
            raise Refused("not https" if hop == 0 else "redirect to a non-https URL")
        if url_contact(url):  # before every hop: a redirect target can carry a contact detail too
            raise Refused("contact detail in the URL" if hop == 0 else "contact detail in a redirect target")
        try:
            host, port = parts.hostname, parts.port or 443
        except ValueError:
            raise Refused("bad port")
        if not host:
            raise Refused("no host")
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        deadline = time.monotonic() + HOP_TIMEOUT  # one deadline per hop, on top of the per-operation socket timeouts
        held: dict = {}
        status, ctype, location, body = within(HOP_TIMEOUT, get_once, host, port, target, deadline, held, held=held)
        if location:
            url = urljoin(url, location)
            continue
        return status, ctype, body
    raise Refused(f"more than {MAX_REDIRECTS} redirects")


def url_contact(url: str) -> list:
    """What (k) finds in the decoded path and query of url: the parts a fetch sends to its host."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return []  # fetch cannot split it either, so it is never sent
    texts = (unquote(parts.path), unquote(parts.query), unquote_plus(parts.query))
    return [what for what, rx in PRIVATE if any(rx.search(t) for t in texts)]


def link_problems(fm: dict, lines: list, warnings: list | None = None) -> list:
    """(links) problems of fm's sources, canonical_works, signals and public_stances; lines is the file.

    Before anything is fetched, every URL to fetch gets the (k) checks on its decoded path and
    query: one match and the (k) lines are all that is returned, with nothing fetched. A (links)
    line names only the host, the line in the file and the reason: never a path, query or title.
    HTTP 403 and 429 are recorded as warnings instead of failures.
    """
    titles: dict = {}
    for s in fm.get("sources") if isinstance(fm.get("sources"), list) else []:
        if isinstance(s, str):
            titles.setdefault(s, None)
    for w in fm.get("canonical_works") if isinstance(fm.get("canonical_works"), list) else []:
        if isinstance(w, dict) and isinstance(w.get("url"), str):
            if titles.get(w["url"]) is None:
                titles[w["url"]] = w.get("title")
    for sig_field in ("recent_signal_12mo", "persistent_signals"):
        for item in fm.get(sig_field) if isinstance(fm.get(sig_field), list) else []:
            if isinstance(item, dict):
                for key in ("url", "evidence_url"):
                    if isinstance(item.get(key), str):
                        titles.setdefault(item[key], None)
    for stance in fm.get("public_stances") if isinstance(fm.get("public_stances"), list) else []:
        if isinstance(stance, dict) and isinstance(stance.get("evidence_url"), str):
            titles.setdefault(stance["evidence_url"], None)
    line = {url: next((n for n, text in enumerate(lines, 1) if url in text), 0) for url in titles}
    found = [f"(k) private-detail: line {line[url]} looks like {what}" for url in titles for what in url_contact(url)]
    if found:
        return list(dict.fromkeys(found))
    out = []
    for url, title in titles.items():
        try:
            host = urlsplit(url).hostname or "no host"
        except ValueError:
            host = "a bad host"
        where = f"(links) {host}, line {line[url]}"
        try:
            status, ctype, body = fetch(url)
        except Refused as e:
            out.append(f"{where}: refused: {e}")
            continue
        except (OSError, http.client.HTTPException, ValueError) as e:  # the class only: an error's text can quote the URL
            out.append(f"{where}: dead: {e.__class__.__name__}")
            continue
        if status in (403, 429):
            if warnings is not None:
                warnings.append(f"{where}: warning: HTTP {status}")
        elif status != 200:
            out.append(f"{where}: dead: HTTP {status}")
        elif title and "html" in ctype.lower():
            # [^<>]: a '<' with no '>' before the next '<' fails after one short scan, so a page full
            # of stray brackets is one pass (the old [^>]+ rescanned to the end of the page from each).
            page = norm(html.unescape(re.sub(r"<[^<>]*>", " ", body.decode("utf-8", "replace"))))
            if norm(title) not in page:
                out.append(f"{where}: title not found on the page")
    return out


def check(path: Path, label: str, cache: dict, optout: set = frozenset(), links: bool = False,
          warnings: list | None = None) -> list:
    try:
        text = read_file(path)
    except (OSError, UnicodeDecodeError) as e:
        return [f"(a) frontmatter: cannot read file: {e}"]
    fm = parse_frontmatter(text)
    if fm is None:
        return ["(a) frontmatter: no '---' frontmatter block at the top"]
    out = []
    held = fm.get("status") == "held"
    missing = [k for k in REQUIRED if not fm.get(k) and not (held and k in HELD_MAY_EMPTY)]
    if missing:
        out.append(f"(a) frontmatter: missing or empty fields: {', '.join(missing)}")
    real = fm.get("real_name")  # a list or mapping is non-empty, so it passes the check above but is never hashed for (j)
    if real and not (isinstance(real, str) and norm(real)):
        out.append("(a) frontmatter: real_name must be one non-empty text value")

    src = fm.get("sources") if isinstance(fm.get("sources"), list) else []
    if len(src) < 3 and not held:
        out.append(f"(b) sources: {len(src)} source URLs, need at least 3")
    bad = [str(i) for i, s in enumerate(src, 1) if not (isinstance(s, str) and s.startswith("https://"))]
    if bad and not held:  # item numbers only: a value could carry a private detail
        out.append(f"(b) sources: {len(bad)} not https:// (items {', '.join(bad)})")

    body = text.split("\n")
    quotes = [n for n, line in enumerate(body) if QUOTE.match(line)]
    name = fm.get("real_name") or "<Name>"
    named = label.replace("<Name>", str(name))
    if quotes and named not in text:
        out.append(f"(c) label: speaks as {name} (line {quotes[0] + 1}) but lacks the label line: {named}")

    slugs = roster_slugs(path.resolve().parent.parent, cache) if path.resolve().parent.name == "personas" else None
    slug = fm.get("slug")
    if slugs is None and not held:
        out.append("(d) roster: no readable registry.json or roster.json beside this personas/ folder")
    elif slugs is not None and slug not in slugs and not held:
        out.append(f"(d) roster: slug '{slug}' is not listed in its department's registry/roster")

    for n in quotes:
        if not SOURCED.search(" ".join(body[n:n + 2])):
            out.append(f"(e) quote: line {n + 1} has no https:// source, [paraphrase] or [extrapolated] on it or the next line")

    stances = fm.get("public_stances") if isinstance(fm.get("public_stances"), list) else []
    uncited = [str(i) for i, s in enumerate(stances) if isinstance(s, dict) and not s.get("evidence_url")]
    if uncited:
        out.append(f"(f) stances: public_stances without evidence_url at index {', '.join(uncited)}")

    field = "persistent_signals" if fm.get("status") == "archetype" else "recent_signal_12mo"
    sig = fm.get(field) if isinstance(fm.get(field), list) else []
    if len(sig) < 2 and not held:
        out.append(f"(g) signals: {field} has {len(sig)}, need at least 2")
    surnames = surname_tokens(fm)
    for sig_field in ("recent_signal_12mo", "persistent_signals"):
        items = fm.get(sig_field) if isinstance(fm.get(sig_field), list) else []
        untitled = [str(i) for i, item in enumerate(items, 1)
                    if not (isinstance(item, dict) and isinstance(item.get("title"), str) and item["title"].strip())]
        if untitled:
            out.append(f"(g) signals: {sig_field} missing title (items {', '.join(untitled)})")
        if surnames and warnings is not None:
            for i, item in enumerate(items, 1):
                if not (isinstance(item, dict) and isinstance(item.get("title"), str) and item["title"].strip()):
                    continue
                takeaway = item.get("takeaway") if isinstance(item.get("takeaway"), str) else ""
                hay_words = set(WORD_TOK.findall(fold_name(f"{item['title']} {takeaway}")))
                if not (surnames & hay_words):
                    warnings.append(f"(g) signals: warning: {sig_field} item {i} title/takeaway has no surname match")

    if slugs is not None:
        # Pairs may cross departments (the meta-orchestrator convenes across teams).
        board = path.resolve().parent.parent.parent
        pool = set().union(*(roster_slugs(d, cache) or set() for d in board.iterdir() if d.is_dir()), held_slugs(board, cache))
        for fld in ("pairs_well_with", "productive_conflict_with"):
            vals = fm.get(fld) if isinstance(fm.get(fld), list) else []
            off = [v for v in vals if isinstance(v, str) and v not in pool]
            if off:
                out.append(f"(h) pairs: {fld} names slugs not in any department roster: {', '.join(off)}")

    me, shared = path.resolve(), {}
    seat = (slug, me.parent.parent.name)
    for key in identity(fm):
        for other, other_slug in board_identities(cache).get(key, []):
            twin = (other_slug, other.parent.parent.name)
            if other != me and not (slug == other_slug and seat != twin and {seat, twin} <= TWO_TEAM_SEATS):
                shared.setdefault(other, set()).add(key[0])
    for other, kinds in sorted(shared.items()):
        what = " and ".join(k for k in ("slug", "name") if k in kinds)
        out.append(f"(i) duplicate: {what} also used by {other.relative_to(BOARD.resolve()).as_posix()}")

    if isinstance(real, str) and hashlib.sha256(norm(real).encode("utf-8")).hexdigest() in optout:
        out.append("(j) opted-out: this person asked not to be included (docs/personas/TAKEDOWN.md)")

    for n, line in enumerate(body):  # only the line number and the rule are printed, never the text
        if len(line) > MAX_LINE:
            out.append(f"(k) private-detail: line {n + 1} is over {MAX_LINE} characters, not scanned")
            continue
        visible = URL_TEXT.sub(" ", line)
        urls = [unquote(u) for u in URL_TEXT.findall(line)]  # a URL's path and query can carry an address too
        for what, rx in PRIVATE:
            if rx.search(visible) or any(rx.search(u) for u in urls):
                out.append(f"(k) private-detail: line {n + 1} looks like {what}")

    if links and not any(o.startswith("(k)") for o in out):  # a file that may hold a private detail sends none of its URLs anywhere
        out += link_problems(fm, body, warnings)
    return out


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    opts = [a for a in argv if a.startswith("--")]
    unknown = [o for o in opts if o not in ("--all", "--links")]
    if unknown:
        print(f"check-personas: unknown option {unknown[0]}", file=sys.stderr)
        return 2
    files = [a for a in argv if not a.startswith("--")]
    if "--all" in opts:
        files += [os.path.relpath(p) for p in sorted(BOARD.glob("*/personas/*.md"))]
    files = list(dict.fromkeys(files))
    if not files:
        print("check-personas: no persona files given (pass files or --all)", file=sys.stderr)
        return 2
    label, cache, fails = label_template(), {}, 0
    optout, links = load_optout(), "--links" in opts
    for f in files:
        warns: list = []
        problems = check(Path(f), label, cache, optout, links, warns)
        fails += bool(problems)
        for p in problems:
            print(f"{f}: {p}")
        for w in warns:
            print(f"{f}: {w}", file=sys.stderr)
    print(f"check-personas: {len(files) - fails}/{len(files)} pass", file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
