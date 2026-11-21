#!/usr/bin/env python3
"""Checker for Super Intelligence persona files (stdlib only; offline unless --links).

Usage:
  python3 scripts/check-personas.py [--all] [--links] [<persona.md> ...]

  --all     check every systems/superintelligence/*/personas/*.md file
  --links   also fetch each source and canonical_works URL (network, opt-in)

Prints one line per problem, "<file>: (<rule>) <name>: <detail>", and exits 1
if there is any problem, 0 if every file passes, 2 on a setup error.

Rules (taken from the existing validate_persona.py / validate_offline.py copies,
templates/attribution.md and the real persona files):
  (a) frontmatter   parses, and has every field all shipped personas carry, non-empty
  (b) sources       at least 3 sources, each an https:// URL
  (c) label         a file that speaks in the person's voice (a `> "..."` block)
                    carries the approved label line from templates/attribution.md
  (d) roster        the slug is listed in its department's registry.json / roster.json
  (e) quote         every `> "..."` line has an https:// URL, [paraphrase] or
                    [extrapolated] on the same or the next line
  (f) stances       every public_stances entry has an evidence_url
  (g) signals       active: >= 2 recent_signal_12mo; archetype: >= 2 persistent_signals
  (h) pairs         pairs_well_with / productive_conflict_with name slugs listed in
                    some department's roster
  (i) duplicate     slug, real_name and aliases (case-folded) are not used by any
                    other persona file on the board, in any department (except the
                    grandfathered two-team seats in TWO_TEAM_SEATS)
  (j) opted-out     the sha256 of the case-folded, space-collapsed real_name is not
                    in docs/personas/optout.sha256 (a missing file is an empty list)
  (k) private-detail  no line looks like a phone number, a street address or a
                    personal (non-work) email address
  (links)           with --links: each URL answers 200 over https, and each
                    canonical_works title appears on its HTML page

--links fetch safety: https only, on the first URL and every redirect hop; every
address each host resolves to must be public (stdlib ipaddress), and the
connection goes to the address that was checked, with no second lookup; 10 s
connect, 10 s read, at most 5 redirects, 2 MB read per page. A refused link
prints "(links) <url>: refused: <reason>" and is never fetched.
"""
from __future__ import annotations

import hashlib
import html
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "systems" / "superintelligence"
ATTRIBUTION = BOARD / "templates" / "attribution.md"
OPTOUT = ROOT / "docs" / "personas" / "optout.sha256"

CONNECT_TIMEOUT = READ_TIMEOUT = 10  # seconds
MAX_REDIRECTS = 5
MAX_BYTES = 2 * 1024 * 1024
REDIRECTS = (301, 302, 303, 307, 308)

# (k) ponytail: regex only; the second read catches what these miss. A PII
# library is the upgrade if second reads keep finding misses.
URL_TEXT = re.compile(r"\b[a-z][a-z0-9+.-]*://\S+|\bwww\.\S+", re.I)
PRIVATE = [
    ("a phone number", re.compile(
        r"(?<![\w.+/-])(?:\+\d{1,3}[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]\d{3}[ .-]\d{4}(?![\w-])"
        r"|(?<![\w.+/-])\+\d{1,3}(?:[ .-]\d{2,4}){2,4}(?![\w-])")),
    ("a street address", re.compile(
        r"\b\d{1,5}(?:\s+[A-Z][a-z]+){1,3}\s+"
        r"(?:Street|Avenue|Ave\.|Road|Boulevard|Blvd\.|Lane|Drive|Court|Terrace|Parkway)\b")),
    ("a personal email address", re.compile(
        r"[\w.+-]+@(?:gmail|googlemail|yahoo|ymail|hotmail|outlook|live|msn|aol|icloud|me|mac"
        r"|proton|protonmail|pm|gmx|mail|yandex|zoho|qq|163|126|fastmail|hey)\.[a-z.]{2,6}\b", re.I)),
]

# The fields every one of the 495 shipped personas has, non-empty.
REQUIRED = ["slug", "real_name", "archetype", "teams", "cell", "cell_role", "status",
            "domains", "signature_moves", "canonical_works", "public_stances",
            "voice_style", "confidence", "sources"]

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
    if s[:1] in "'\"" and s[-1:] == s[:1] and len(s) > 1:
        return s[1:-1]
    s = re.sub(r"\s+#.*$", "", s)
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


def roster_slugs(dept: Path, cache: dict):
    if dept not in cache:
        slugs, found = set(), False
        for name in ("registry.json", "roster.json"):
            p = dept / name
            if p.is_file():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
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
        m = re.search(r"\*\*<Name> persona\*\*: [^\n]*", ATTRIBUTION.read_text(encoding="utf-8"))
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
                fm = parse_frontmatter(p.read_text(encoding="utf-8")) or {}
            except (OSError, UnicodeDecodeError):
                continue  # this file reports its own (a) when it is checked
            for key in identity(fm):
                index.setdefault(key, []).append((p.resolve(), fm.get("slug")))
        cache["identities"] = index
    return cache["identities"]


def load_optout() -> set:
    try:
        text = OPTOUT.read_text(encoding="utf-8")
    except FileNotFoundError:
        return set()
    except (OSError, UnicodeDecodeError) as e:
        print(f"{OPTOUT}: cannot read: {e}", file=sys.stderr)
        sys.exit(2)
    rows = [r.strip().lower() for r in text.splitlines() if r.strip() and not r.lstrip().startswith("#")]
    bad = [r for r in rows if not re.fullmatch(r"[0-9a-f]{64}", r)]
    if bad:  # a malformed line would silently match no one: fail closed
        print(f"{OPTOUT}: not a sha256 hex line: {bad[0][:20]}", file=sys.stderr)
        sys.exit(2)
    return set(rows)


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
    except (OSError, UnicodeError) as e:
        raise Refused(f"cannot resolve {host}: {e}")
    addrs = [ipaddress.ip_address(info[4][0].split("%")[0]) for info in infos]
    if not addrs:
        raise Refused(f"cannot resolve {host}: no addresses")
    for a in addrs:
        if not is_public(a):
            raise Refused(f"{host} resolves to non-public address {a}")
    return str(addrs[0])


class PinnedHTTPS(http.client.HTTPSConnection):
    """HTTPS to an address already checked: no second lookup of the host name."""

    def __init__(self, host: str, port: int, address: str):
        super().__init__(host, port, timeout=READ_TIMEOUT)
        self.address, self.tls = address, ssl.create_default_context()

    def connect(self):
        sock = socket.create_connection((self.address, self.port), timeout=CONNECT_TIMEOUT)
        try:
            sock.settimeout(READ_TIMEOUT)
            self.sock = self.tls.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


def fetch(url: str):
    """GET url under the fetch-safety rules. Returns (status, content_type, body)."""
    for hop in range(MAX_REDIRECTS + 1):
        parts = urlsplit(url)
        if parts.scheme != "https":
            raise Refused(f"not https: {url}" if hop == 0 else f"redirect to non-https {url}")
        try:
            host, port = parts.hostname, parts.port or 443
        except ValueError:
            raise Refused(f"bad port in {url}")
        if not host:
            raise Refused(f"no host in {url}")
        conn = PinnedHTTPS(host, port, checked_address(host, port))
        try:
            conn.request("GET", (parts.path or "/") + (f"?{parts.query}" if parts.query else ""),
                         headers={"User-Agent": "coco-check-personas", "Accept": "text/html,*/*"})
            resp = conn.getresponse()
            location = resp.getheader("Location")
            if resp.status in REDIRECTS and location:
                url = urljoin(url, location)
                continue
            return resp.status, resp.getheader("Content-Type") or "", resp.read(MAX_BYTES)
        finally:
            conn.close()
    raise Refused(f"more than {MAX_REDIRECTS} redirects")


def link_problems(fm: dict) -> list:
    titles: dict = {}
    for s in fm.get("sources") if isinstance(fm.get("sources"), list) else []:
        if isinstance(s, str):
            titles.setdefault(s, None)
    for w in fm.get("canonical_works") if isinstance(fm.get("canonical_works"), list) else []:
        if isinstance(w, dict) and isinstance(w.get("url"), str):
            if titles.get(w["url"]) is None:
                titles[w["url"]] = w.get("title")
    out = []
    for url, title in titles.items():
        try:
            status, ctype, body = fetch(url)
        except Refused as e:
            out.append(f"(links) {url}: refused: {e}")
            continue
        except (OSError, http.client.HTTPException, ValueError) as e:
            out.append(f"(links) {url}: dead: {e.__class__.__name__}: {e}")
            continue
        if status != 200:
            out.append(f"(links) {url}: dead: HTTP {status}")
        elif title and "html" in ctype.lower():
            page = norm(html.unescape(re.sub(r"<[^>]+>", " ", body.decode("utf-8", "replace"))))
            if norm(title) not in page:
                out.append(f"(links) {url}: title not found on the page: {title}")
    return out


def check(path: Path, label: str, cache: dict, optout: set = frozenset(), links: bool = False) -> list:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"(a) frontmatter: cannot read file: {e}"]
    fm = parse_frontmatter(text)
    if fm is None:
        return ["(a) frontmatter: no '---' frontmatter block at the top"]
    out = []
    missing = [k for k in REQUIRED if not fm.get(k)]
    if missing:
        out.append(f"(a) frontmatter: missing or empty fields: {', '.join(missing)}")

    src = fm.get("sources") if isinstance(fm.get("sources"), list) else []
    if len(src) < 3:
        out.append(f"(b) sources: {len(src)} source URLs, need at least 3")
    bad = [s for s in src if not (isinstance(s, str) and s.startswith("https://"))]
    if bad:
        out.append(f"(b) sources: not https://: {', '.join(map(str, bad[:3]))}")

    body = text.split("\n")
    quotes = [n for n, line in enumerate(body) if QUOTE.match(line)]
    name = fm.get("real_name") or "<Name>"
    named = label.replace("<Name>", str(name))
    if quotes and named not in text:
        out.append(f"(c) label: speaks as {name} (line {quotes[0] + 1}) but lacks the label line: {named}")

    slugs = roster_slugs(path.resolve().parent.parent, cache) if path.resolve().parent.name == "personas" else None
    slug = fm.get("slug")
    if slugs is None:
        out.append("(d) roster: no readable registry.json or roster.json beside this personas/ folder")
    elif slug not in slugs:
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
    if len(sig) < 2:
        out.append(f"(g) signals: {field} has {len(sig)}, need at least 2")

    if slugs is not None:
        # Pairs may cross departments (the meta-orchestrator convenes across teams).
        pool = set().union(*(roster_slugs(d, cache) or set() for d in path.resolve().parent.parent.parent.iterdir() if d.is_dir()))
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

    if isinstance(fm.get("real_name"), str) and \
            hashlib.sha256(norm(fm["real_name"]).encode("utf-8")).hexdigest() in optout:
        out.append("(j) opted-out: this person asked not to be included (docs/personas/TAKEDOWN.md)")

    for n, line in enumerate(body):
        visible = URL_TEXT.sub(" ", line)
        for what, rx in PRIVATE:
            if rx.search(visible):
                out.append(f"(k) private-detail: line {n + 1} looks like {what}")

    if links:
        out += link_problems(fm)
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
        problems = check(Path(f), label, cache, optout, links)
        fails += bool(problems)
        for p in problems:
            print(f"{f}: {p}")
    print(f"check-personas: {len(files) - fails}/{len(files)} pass", file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
