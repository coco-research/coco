#!/usr/bin/env python3
"""Report upstream drift in the code this repository vendors.

data/vendor-lock.json records what CoCo took from upstream: the repo, the
pinned ref, the vendored paths, and the licence digests. This script asks the
next question: has upstream moved since?

For every row it reads `git ls-remote` (30 s timeout) for the default-branch
HEAD and the newest tag. When either differs from `pinned_ref`, it fetches that
ref and the pin into a throwaway directory under mktemp and diffs the files
under the row's `paths`. Nothing is written to the repository. A pin that
resolves through `refs/tags/` is a release pin, so it is compared only with the
newest tag: later commits on the default branch are not drift.

This is a manual or maintainer tool, not a per-pull-request CI job. A pin to a
commit sha that no ref advertises makes it fetch every branch and tag with full
history, capped only by the fetch timeout, and paying that on every pull request
buys nothing when the report gates nothing.

One status per row:
  current      nothing upstream advertises is newer than the pin;
  drift        a newer ref exists; the other fields describe what moved;
  unreachable  `git ls-remote` failed, or the new ref could not be fetched;
  unknown-pin  `pinned_ref` is absent or "unknown", or no longer resolves.

`changed_files` counts the files upstream changed under the row's `paths`
between the pin and the new ref, so it measures upstream movement, not local
edits (tests/check-vendor-lock.py owns the local side). `licence_changed`
compares the sha256 of the upstream licence files on both sides. `risky_lines`
counts added lines matching curl|wget|pip install|npm i|api[_-]?key|cookie:
that is the question a new pin raises for a reviewer, not a verdict.

`paths` are matched against the upstream tree as written. That is exact for a
row whose vendored layout mirrors upstream, and reports zero files for a row
rearranged on the way in. The new ref still surfaces as drift, so the review
still happens, with a smaller `changed_files` than reality.

This reports; it does not gate. Exit 0 whatever it finds, and 2 when the lock
cannot be read or does not have the shape described above.

Run from the repository root:
  python3 scripts/vendor-check.py
  python3 scripts/vendor-check.py --lock data/vendor-lock.json --json
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCK = ROOT / "data" / "vendor-lock.json"

LS_REMOTE_TIMEOUT = 30
FETCH_TIMEOUT = 120

MAX_LICENCES = 20
LICENCE_NAMES = frozenset({
    "LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md",
    "COPYING", "COPYING.txt", "NOTICE", "NOTICE.md",
})

# The patterns a reviewer should look at when a pin moves: network fetches,
# package installs and credential-shaped strings. Case-insensitive so
# "PIP INSTALL" in a README does not slip past.
RISKY = re.compile(r"curl|wget|pip install|npm i|api[_-]?key|cookie", re.I)

# Fetch every branch tip and tag, with full history. Used only when the pin is
# a commit that is not itself a ref tip and the remote refuses a bare sha.
ALL_REFS = ["+refs/heads/*:refs/remotes/vendor/heads/*",
            "+refs/tags/*:refs/tags/*"]

# file:// exists for tests/check-vendor-check.sh only, which builds its fake
# upstream in mktemp. A real run speaks https and nothing else, so a lock row
# cannot point git at a local path.
ALLOW_FILE = os.environ.get("COCO_VENDOR_CHECK_ALLOW_FILE") == "1"

# The caller's config is not part of the question this script asks, and
# `protocol.allow=never` stops a repo value from selecting any transport that
# is not allowed right after it.
GIT_CONFIG = ["-c", "protocol.allow=never",
              "-c", "protocol.https.allow=always"]
if ALLOW_FILE:
    GIT_CONFIG += ["-c", "protocol.file.allow=always"]

ENV = dict(os.environ,
           GIT_TERMINAL_PROMPT="0",
           GIT_CONFIG_NOSYSTEM="1",
           GIT_CONFIG_GLOBAL="/dev/null")

HEX = re.compile(r"[0-9a-fA-F]{7,40}")


def git(args, cwd=None, timeout=FETCH_TIMEOUT, binary=False):
    """Run git isolated from local config; None when it cannot run at all.

    Every git call goes through here, so every one gets the same `-c` policy
    and the same environment. A repo argument is always passed after `--`.
    """
    try:
        return subprocess.run(["git", *GIT_CONFIG, *args], cwd=cwd, env=ENV,
                              timeout=timeout, capture_output=True,
                              text=not binary)
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return None


def remote_refs(repo):
    """({ref name: sha}, default branch ref) from ls-remote, or (None, None).

    Runs in a throwaway directory rather than the caller's checkout: a repo
    value must not be able to resolve against, or run inside, the working tree
    this script was started from.
    """
    with tempfile.TemporaryDirectory(prefix="vendor-check-ls-") as cwd:
        done = git(["ls-remote", "--symref", "--", repo], cwd=cwd,
                   timeout=LS_REMOTE_TIMEOUT)
    if done is None or done.returncode != 0:
        return None, None
    refs, default = {}, None
    for line in done.stdout.splitlines():
        meta, _, name = line.partition("\t")
        name = name.strip()
        if not name:
            continue
        if meta.startswith("ref: "):
            if name == "HEAD":
                default = meta[len("ref: "):].strip()
            continue
        refs[name] = meta.strip()
    return refs, default


def version_key(tag):
    """Sort tags by their numbers, so v10 follows v9 rather than v1."""
    return [(0, int(part)) if part.isdigit() else (1, part)
            for part in re.split(r"(\d+)", tag) if part]


def newest_tag(refs):
    """(tag, commit sha) for the highest-sorting tag, or None."""
    tags = {}
    for name, sha in refs.items():
        if not name.startswith("refs/tags/"):
            continue
        tag = name[len("refs/tags/"):]
        if tag.endswith("^{}"):
            tags[tag[:-3]] = sha        # the peeled commit wins
        else:
            tags.setdefault(tag, sha)
    if not tags:
        return None
    tag = max(tags, key=version_key)
    return tag, tags[tag]


def resolve(refs, pinned):
    """The commit `pinned` names, or None. A sha may be abbreviated."""
    for name in (pinned, "refs/tags/" + pinned, "refs/heads/" + pinned):
        sha = refs.get(name)
        if sha:
            return refs.get(name + "^{}", sha)
    if HEX.fullmatch(pinned):
        want = pinned.lower()
        # Peeling first: an annotated tag also advertises its tag object, and
        # the commit is the one a pin means.
        for group in ([sha for name, sha in refs.items()
                       if name.endswith("^{}")], list(refs.values())):
            for sha in group:
                if sha.startswith(want):
                    return sha
    return None


def git_spec(pattern):
    """A lock glob as a git pathspec. `dir/**` is `dir`, `**` is the tree."""
    path = pattern.strip()
    if path in ("", ".", "*", "**"):
        return "."
    if path.endswith("/**"):
        path = path[:-3]
    elif path.endswith("/*"):
        path = path[:-2]
    return path.rstrip("/") or "."


def ensure_repo(dest):
    done = git(["init", "-q", dest])
    return done is not None and done.returncode == 0


def fetch(dest, repo, refspecs, depth=True):
    args = ["fetch", "--quiet"]
    if depth:
        args += ["--depth", "1"]
    args += ["--", repo, *refspecs]
    done = git(args, cwd=dest)
    return done is not None and done.returncode == 0


def fetch_commit(dest, repo, ref):
    """Shallow-fetch one ref into dest; its commit sha, or None."""
    if not fetch(dest, repo, [ref]):
        return None
    done = git(["rev-parse", "--verify", "FETCH_HEAD^{commit}"], cwd=dest)
    if done is None or done.returncode != 0:
        return None
    return done.stdout.strip()


def matches(sha, pinned, resolved):
    """Does `sha` name the pinned commit? An unadvertised sha pin is textual."""
    if resolved is not None:
        return sha == resolved
    return sha.lower().startswith(pinned.lower())


def fetch_pinned(dest, repo, pinned, resolved, refs):
    """The pinned commit's sha in dest, or None when it cannot be obtained.

    A tag, branch or tip pin is fetched by the ref name ls-remote advertised,
    which is a shallow fetch. An older sha is not advertised at all, so the
    last attempt takes the history instead of the tip.
    """
    attempts = []
    if resolved is not None:
        attempts = [name for name, sha in refs.items()
                    if sha == resolved and not name.endswith("^{}")]
    attempts += [pinned, "refs/tags/" + pinned, "refs/heads/" + pinned]
    for ref in dict.fromkeys(attempts):
        sha = fetch_commit(dest, repo, ref)
        if sha:
            return sha
    if HEX.fullmatch(pinned):
        if fetch(dest, repo, ALL_REFS, depth=False):
            done = git(["rev-parse", "--verify", pinned + "^{commit}"], cwd=dest)
            if done is not None and done.returncode == 0:
                return done.stdout.strip()
    return None


def compare(dest, old, new, specs):
    """(changed file count, risky added line count) between two commits.

    Both commits live in dest. A shallow fetch makes each one a root; git diff
    compares trees, so no common ancestor is needed.
    """
    scope = specs or ["."]
    names = git(["diff", "--name-only", "--no-renames", old, new, "--", *scope],
                cwd=dest)
    changed = 0
    if names is not None and names.returncode == 0:
        changed = sum(1 for line in names.stdout.splitlines() if line.strip())
    patch = git(["diff", "--unified=0", "--no-color", "--no-renames",
                 old, new, "--", *scope], cwd=dest)
    risky = 0
    if patch is not None and patch.returncode == 0:
        for line in patch.stdout.splitlines():
            if (line.startswith("+") and not line.startswith("+++ ")
                    and RISKY.search(line)):
                risky += 1
    return changed, risky


def read_blob(dest, commit, rel):
    """The bytes of `rel` at `commit`, or None when it is not a file there."""
    if not rel or rel.endswith("/"):
        return None
    done = git(["show", f"{commit}:{rel}"], cwd=dest, binary=True)
    if done is None or done.returncode != 0:
        return None
    return done.stdout


def licence_prefixes(specs):
    """The in-repo subtrees a row covers, for finding its licence upstream."""
    prefixes = []
    for spec in specs:
        if spec == ".":
            return [""]
        prefixes.append(spec.rstrip("/") + "/")
    return prefixes


def licence_digests(dest, commit, wanted, prefixes):
    """{path: sha256} for the licence files this row would care about.

    The lock's licence paths come first: they name the copies this repo keeps,
    which upstream usually holds at the same place. When none of them exist
    there, fall back to licence-named files at the repository root and under
    the row's own subtrees, so a license that moved inside upstream is still
    caught without hashing every LICENSE in a fonts-sized repository.
    """
    found = {}
    for rel in wanted:
        data = read_blob(dest, commit, rel)
        if data is not None:
            found[rel] = hashlib.sha256(data).hexdigest()
    if found:
        return found

    listing = git(["ls-tree", "-r", "--name-only", "-z", commit], cwd=dest)
    if listing is None or listing.returncode != 0:
        return {}
    paths = [p for p in listing.stdout.split("\0") if p]
    candidates = [
        path for path in paths
        if Path(path).name in LICENCE_NAMES
        and ("/" not in path or any(path.startswith(p) for p in prefixes))
    ][:MAX_LICENCES]
    for path in candidates:
        data = read_blob(dest, commit, path)
        if data is not None:
            found[path] = hashlib.sha256(data).hexdigest()
    return found


def check_row(row):
    result = {
        "name": str(row.get("name", "")).strip(),
        "status": "unreachable",
        "new_ref": "",
        "changed_files": 0,
        "licence_changed": False,
        "risky_lines": 0,
    }

    pinned = str(row.get("pinned_ref") or "").strip()
    if not pinned or pinned.lower() == "unknown":
        result["status"] = "unknown-pin"
        return result

    refs, default = remote_refs(str(row.get("repo", "")).strip())
    if refs is None:
        return result

    pinned_sha = resolve(refs, pinned)
    if pinned_sha is None and not HEX.fullmatch(pinned):
        # A tag or branch that ls-remote no longer advertises cannot be read.
        # A sha can be an old commit that no ref points at any more, which is
        # not an unknown pin: the fetch below decides.
        result["status"] = "unknown-pin"
        return result

    candidates = []
    tag = newest_tag(refs)
    if "refs/tags/" + pinned in refs:
        # A tag pin tracks releases. The default branch moving past the pin is
        # what the next release will contain, not a change to what is pinned.
        if tag:
            candidates.append((tag[0], tag[1], "refs/tags/" + tag[0]))
    else:
        head_sha = refs.get("HEAD")
        if head_sha:
            label = default.rsplit("/", 1)[-1] if default else "HEAD"
            candidates.append((label, head_sha, default or "HEAD"))
        if tag:
            candidates.append((tag[0], tag[1], "refs/tags/" + tag[0]))

    if not candidates:
        # ls-remote answered, but with no ref at all: an empty or unborn
        # remote cannot tell us the pin is current.
        result["status"] = "unknown-pin"
        return result

    chosen = next(((label, refspec) for label, sha, refspec in candidates
                   if not matches(sha, pinned, pinned_sha)), None)
    if chosen is None:
        result["status"] = "current"
        return result

    label, refspec = chosen
    result["status"] = "drift"
    result["new_ref"] = label

    paths = [p for p in row.get("paths") or []
             if isinstance(p, str) and p.strip()]
    specs = [git_spec(p) for p in paths]
    wanted = [entry["path"] for entry in row.get("licence_files") or []
              if isinstance(entry, dict) and isinstance(entry.get("path"), str)]
    repo = str(row.get("repo", "")).strip()

    with tempfile.TemporaryDirectory(prefix="vendor-check-") as tmp:
        if not ensure_repo(tmp):
            return result
        old = fetch_pinned(tmp, repo, pinned, pinned_sha, refs)
        if old is None:
            result["status"] = "unknown-pin"
            result["new_ref"] = label
            return result
        new = fetch_commit(tmp, repo, refspec)
        if new is None:
            result["status"] = "unreachable"
            result["new_ref"] = label
            return result
        result["changed_files"], result["risky_lines"] = compare(
            tmp, old, new, specs)
        prefixes = licence_prefixes(specs)
        result["licence_changed"] = (
            licence_digests(tmp, old, wanted, prefixes)
            != licence_digests(tmp, new, wanted, prefixes))
    return result


def load(path):
    """The lock's rows, or None after explaining why it is invalid."""
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"vendor-check: cannot read {path}: {exc}", file=sys.stderr)
        return None
    except (UnicodeError, json.JSONDecodeError) as exc:
        print(f"vendor-check: {path} is not valid JSON: {exc}", file=sys.stderr)
        return None
    if not isinstance(rows, list):
        print(f"vendor-check: {path} must be a JSON array of rows",
              file=sys.stderr)
        return None
    for index, row in enumerate(rows):
        where = f"row {index}"
        if not isinstance(row, dict):
            print(f"vendor-check: {where} must be an object", file=sys.stderr)
            return None
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            print(f"vendor-check: {where} has no name", file=sys.stderr)
            return None
        if not isinstance(row.get("repo"), str) or not row["repo"].strip():
            print(f"vendor-check: row {row['name']!r} has no repo",
                  file=sys.stderr)
            return None
        repo = row["repo"].strip()
        if repo.startswith("-"):
            print(f"vendor-check: row {row['name']!r} has a repo starting with "
                  f"'-': {repo!r}", file=sys.stderr)
            return None
        if not repo.startswith("https://") and not (
                ALLOW_FILE and repo.startswith("file://")):
            print(f"vendor-check: row {row['name']!r} has a repo that is not "
                  f"https://: {repo!r}", file=sys.stderr)
            return None
        paths = row.get("paths")
        if (not isinstance(paths, list) or not paths
                or not all(isinstance(p, str) and p.strip() for p in paths)):
            print(f"vendor-check: row {row['name']!r} has no filesystem paths",
                  file=sys.stderr)
            return None
        if row.get("pinned_ref") is not None and not isinstance(
                row["pinned_ref"], str):
            print(f"vendor-check: row {row['name']!r} has a non-string pinned_ref",
                  file=sys.stderr)
            return None
    return rows


def render(results):
    print(f"{'name':<32} {'status':<12} {'new_ref':<18} "
          f"{'changed':>7} {'licence':>7} {'risky':>5}")
    for row in results:
        print(f"{row['name'][:32]:<32} {row['status']:<12} "
              f"{(row['new_ref'] or '-'):<18} {row['changed_files']:>7} "
              f"{'yes' if row['licence_changed'] else 'no':>7} "
              f"{row['risky_lines']:>5}")
    counts = {}
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    order = ("current", "drift", "unreachable", "unknown-pin")
    print()
    print(f"{len(results)} row(s): "
          + ", ".join(f"{counts.get(status, 0)} {status}" for status in order))


def main(argv):
    parser = argparse.ArgumentParser(
        description="Report drift in vendored upstream code.")
    parser.add_argument("--lock", default=str(DEFAULT_LOCK),
                        help="vendor lock JSON (default: data/vendor-lock.json)")
    parser.add_argument("--json", action="store_true",
                        help="print one JSON object per row")
    args = parser.parse_args(argv)

    rows = load(Path(args.lock))
    if rows is None:
        return 2

    results = [check_row(row) for row in rows]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        render(results)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
