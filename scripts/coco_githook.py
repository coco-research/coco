#!/usr/bin/env python3
"""coco-gate githook: put the coco-workflow pre-commit warning into the git hooks
of the repo of the current directory, keep a pre-commit hook that is already
there by chaining it, and never overwrite a file that is not ours.

Python 3.8+ stdlib only. Every message is one line and no traceback escapes;
exit 0 on success, 1 when refused or on error, 2 on a usage error.

Both commands plan first and apply second, so --dry-run reaches the same
decision without a single write. The hooks dir is scoped to the repo: it must
not be a symlink, and its real path must be inside the git common dir, which
refuses a global core.hooksPath as well as an in-tree one. Ours means
byte-identical to what install wrote, hash line included; anything else is left
where it is. --json prints the plan as one object on stdout and every message
goes to stderr.

  install           write the wrapper, or say it is already there
  install --chain   keep an existing pre-commit hook: it runs after the warning
  remove            take the wrapper out and put the kept hook back

A refusal carries a stable reason: not-a-repo, no-workflow-install,
hooks-dir-symlink, hooks-dir-outside-repo, hardlinked-hook, existing-hook,
chained-name-taken, wrapper-changed, not-coco-wrapper.
"""

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile

MARKER = "# coco-workflow pre-commit wrapper"
CHAINED = "pre-commit.coco-chained"
ZERO_HASH = "0" * 64
HASH_LINE = re.compile(r"^# sha256: ([0-9a-f]{64})$")

WRAPPER = """#!/bin/sh
# coco-workflow pre-commit wrapper
# sha256: %(hash)s
# Written by `coco-gate githook install`; undo with `coco-gate githook remove`.
# Runs the coco-workflow warning, then the chained hook, whose exit code decides.
hook=%(hook)s
chain=%(chain)s
if [ -x "$hook" ]; then COCO_CHAIN_HOOK="$chain" exec "$hook" "$@"; fi
if [ -n "$chain" ]; then exec "$chain" "$@"; fi
exit 0
"""


class GitError(Exception):
    """One line, no traceback: git could not answer."""


class Refusal(Exception):
    """A stable reason, one line to say it, and how far the plan got."""

    def __init__(self, reason, message, hooks_dir=None, existing=None):
        Exception.__init__(self, message)
        self.reason = reason
        self.message = message
        self.hooks_dir = hooks_dir
        self.existing = existing


def say(text, stream=None):
    """One line per message, whatever the text brought with it."""
    print(" ".join(str(text).split()) or "unknown error", file=stream or sys.stdout)


def git(*args):
    """Run git here; return its stdout, stripped. A failure is one short line."""
    try:
        done = subprocess.run(("git",) + args, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True)
    except OSError as exc:
        raise GitError("cannot run git: %s" % exc)
    if done.returncode != 0:
        raise GitError(done.stderr.strip() or "git %s failed" % args[0])
    return done.stdout.strip()


def repo_paths():
    """(hooks dir, git common dir), both absolute. Refused when git can't answer."""
    try:
        # Not --path-format=absolute for the hooks dir: that resolves a symlinked
        # hooks dir to its target, and the symlink check below would never see it.
        # This spelling is relative to here, so abspath (which keeps links) finishes it.
        hooks = git("rev-parse", "--git-path", "hooks")
        try:
            common = git("rev-parse", "--path-format=absolute", "--git-common-dir")
        except GitError:
            common = git("rev-parse", "--git-common-dir")  # git before 2.31
    except GitError as exc:
        raise Refusal("not-a-repo", str(exc))
    return os.path.abspath(hooks), os.path.abspath(common)


def scoped_hooks_dir():
    """The repo's hooks dir, once it is provably a plain dir inside the repo."""
    hooks, common = repo_paths()
    if os.path.islink(hooks):
        raise Refusal("hooks-dir-symlink",
                      "%s is a symlink; refusing to write there" % hooks, hooks)
    real = os.path.realpath(hooks)
    root = os.path.realpath(common)
    if not (real == root or real.startswith(root.rstrip(os.sep) + os.sep)):
        raise Refusal("hooks-dir-outside-repo",
                      "%s is outside %s; refusing to write there" % (real, root), hooks)
    return hooks


def coco_hook():
    """The workflow hook the installer links: <claude_home>/coco/hooks/<name>."""
    home = os.environ.get("CLAUDE_HOME") or os.path.expanduser("~/.claude")
    return os.path.abspath(os.path.join(home, "coco", "hooks",
                                        "coco-workflow-pre-commit.sh"))


def classify(path):
    """(kind, changed): none, symlink, coco-wrapper or file; changed is the
    marker present with a hash that doesn't check out, i.e. not what we wrote."""
    if not os.path.lexists(path):
        return "none", False
    if os.path.islink(path):
        return "symlink", False
    if not os.path.isfile(path):
        return "file", False
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return "file", False
    lines = raw.split(b"\n")
    if len(lines) < 2 or lines[1].decode("utf-8", "replace") != MARKER:
        return "file", False
    match = HASH_LINE.match(lines[2].decode("utf-8", "replace")) if len(lines) > 2 else None
    if not match:  # the marker is there but the hash line is not: not what we wrote
        return "file", True
    # The hash covers these bytes with the 64 hex chars replaced by 64 zeros.
    at = len(lines[0]) + len(lines[1]) + 2 + len("# sha256: ")
    zeroed = raw[:at] + ZERO_HASH.encode("ascii") + raw[at + 64:]
    if hashlib.sha256(zeroed).hexdigest() == match.group(1):
        return "coco-wrapper", False
    return "file", True


def wrapper_bytes(hook, chain):
    """The wrapper with the hash of its own bytes on line three, hex zeroed."""
    fields = {"hook": shlex.quote(hook), "chain": shlex.quote(chain)}
    zeroed = (WRAPPER % dict(fields, hash=ZERO_HASH)).encode("utf-8")
    return (WRAPPER % dict(fields, hash=hashlib.sha256(zeroed).hexdigest())).encode("utf-8")


def write_wrapper(path, hook, chain):
    """Write the wrapper atomically: a temp file here, chmod, then os.replace."""
    body = wrapper_bytes(hook, chain)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".coco-githook.")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(body)
        os.chmod(tmp, 0o755)
        os.replace(tmp, path)  # the directory entry, never through a symlink
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def hardlinked(path):
    """A regular file with a second link: the same file lives somewhere else too."""
    if not os.path.lexists(path) or os.path.islink(path) or not os.path.isfile(path):
        return False
    return os.lstat(path).st_nlink > 1


def plan_install(args):
    """What install would do here, or a Refusal. Writes nothing."""
    hooks = scoped_hooks_dir()
    hook = coco_hook()
    if not (os.path.isfile(hook) and os.access(hook, os.X_OK)):
        raise Refusal("no-workflow-install",
                      "the workflow hooks aren't installed; run the coco installer "
                      "with --workflow first", hooks)
    target = os.path.join(hooks, "pre-commit")
    chained = os.path.join(hooks, CHAINED)
    kind, changed = classify(target)
    plan = {"cmd": "install", "hooks_dir": hooks, "existing": kind, "ops": [],
            "chain": "", "ok": True}
    for path in (target, chained):
        if hardlinked(path):
            raise Refusal("hardlinked-hook",
                          "%s has a second hard link; leaving it as it is" % path,
                          hooks, kind)
    if changed:
        raise Refusal("wrapper-changed",
                      "%s has the coco marker but is not what install wrote; "
                      "leaving it as it is" % target, hooks, kind)
    if kind == "coco-wrapper":
        plan["message"] = "already installed %s" % target
        return plan
    if kind != "none" and not args.chain:
        raise Refusal("existing-hook",
                      "%s already exists. Re-run with --chain to keep it: it runs "
                      "after the warning, and its result decides. Or leave it as it "
                      "is." % target, hooks, kind)
    if kind != "none" and os.path.lexists(chained):
        raise Refusal("chained-name-taken", "%s already exists; move it away first"
                      % chained, hooks, kind)
    if kind == "none":
        plan["ops"].append({"op": "write", "path": target})
        plan["message"] = "installed %s" % target
        return plan
    plan["chain"] = chained
    plan["ops"].append({"op": "rename", "from": target, "to": chained})
    plan["ops"].append({"op": "write", "path": target})
    plan["message"] = ("installed %s; your hook is now %s, runs after the warning, "
                       "and its result decides" % (target, chained))
    return plan


def plan_remove(args):
    """What remove would do here, or a Refusal. Writes nothing."""
    hooks = scoped_hooks_dir()
    target = os.path.join(hooks, "pre-commit")
    chained = os.path.join(hooks, CHAINED)
    kind, changed = classify(target)
    plan = {"cmd": "remove", "hooks_dir": hooks, "existing": kind, "ops": [],
            "chain": "", "ok": True}
    for path in (target, chained):
        if hardlinked(path):
            raise Refusal("hardlinked-hook",
                          "%s has a second hard link; leaving it as it is" % path,
                          hooks, kind)
    if changed:
        raise Refusal("wrapper-changed",
                      "%s has the coco marker but is not what install wrote; "
                      "leaving it as it is" % target, hooks, kind)
    if kind == "none":
        if os.path.lexists(chained):
            # A hand-deleted wrapper must not leave the user's hook parked.
            plan["ops"].append({"op": "rename", "from": chained, "to": target})
            plan["message"] = "removed %s; your hook is back in place" % target
        else:
            plan["message"] = "nothing to remove"
        return plan
    if kind != "coco-wrapper":
        raise Refusal("not-coco-wrapper",
                      "%s is not the coco wrapper; leaving it as it is" % target,
                      hooks, kind)
    plan["ops"].append({"op": "delete", "path": target})
    if os.path.lexists(chained):
        plan["ops"].append({"op": "rename", "from": chained, "to": target})
        plan["message"] = "removed %s; your hook is back in place" % target
    else:
        plan["message"] = "removed %s" % target
    return plan


def apply(plan):
    """Carry the plan out. Returns a one-line failure message, or None."""
    hooks = plan["hooks_dir"]
    target = os.path.join(hooks, "pre-commit")
    if plan["ops"] and not os.path.isdir(hooks):
        os.makedirs(hooks)  # only when missing, only after the scope checks
    moved = ""
    for op in plan["ops"]:
        if op["op"] == "rename":
            os.rename(op["from"], op["to"])  # a symlink moves as a link
            if op["from"] == target:
                moved = op["to"]
        elif op["op"] == "delete":
            os.unlink(op["path"])
        else:
            try:
                write_wrapper(op["path"], coco_hook(), plan["chain"])
            except Exception as exc:
                if moved:
                    os.rename(moved, target)  # the hook that was here goes back
                return "could not write %s: %s" % (op["path"], exc)
    return None


def refused(args, reason, message, plan=None):
    """The plan-shaped answer for a refusal or an error."""
    plan = plan or {}
    return {"cmd": args.cmd, "hooks_dir": plan.get("hooks_dir"),
            "existing": plan.get("existing"), "ops": [], "ok": False,
            "reason": reason, "message": message}


def op_text(op):
    if op["op"] == "rename":
        return "rename %s to %s" % (op["from"], op["to"])
    return "%s %s" % (op["op"], op["path"])


def report(plan, args):
    """One JSON object on stdout, or the one-line text; never both."""
    if args.json:
        out = {"cmd": plan["cmd"], "dry_run": bool(args.dry_run),
               "hooks_dir": plan["hooks_dir"], "existing": plan["existing"],
               "ops": plan["ops"], "ok": plan["ok"]}
        if not plan["ok"]:
            out["reason"] = plan["reason"]
            out["message"] = plan["message"]
        print(json.dumps(out, sort_keys=True))
        if plan["message"]:
            say(plan["message"], sys.stderr)
    elif args.dry_run and plan["ops"]:
        for op in plan["ops"]:
            say("would " + op_text(op))
    elif plan["message"]:
        say(plan["message"])
    return 0 if plan["ok"] else 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="coco-gate githook",
        description="Put the coco-workflow pre-commit warning in this repo's git "
                    "hooks. A pre-commit hook that is already there is kept by "
                    "chaining it, never overwritten.")
    subs = parser.add_subparsers(dest="cmd")
    install = subs.add_parser("install", help="write the pre-commit wrapper here")
    install.add_argument("--chain", action="store_true",
                         help="keep an existing pre-commit hook: it runs after the "
                              "warning, and its result decides")
    remove = subs.add_parser("remove", help="take the wrapper out and put your hook back")
    for sub in (install, remove):
        sub.add_argument("--dry-run", action="store_true",
                         help="say what would happen and write nothing")
        sub.add_argument("--json", action="store_true",
                         help="print the plan as one JSON object on stdout; messages "
                              "go to stderr")
    return parser


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 2
    plan = None
    try:
        plan = {"install": plan_install, "remove": plan_remove}[args.cmd](args)
        if plan["ok"] and not args.dry_run:
            failure = apply(plan)
            if failure:
                plan["ok"], plan["reason"], plan["message"] = False, "error", failure
                plan["ops"] = []  # nothing is left half done that the caller can see
    except Refusal as exc:
        plan = refused(args, exc.reason, exc.message,
                       {"hooks_dir": exc.hooks_dir, "existing": exc.existing})
    except GitError as exc:  # not-a-repo, if it ever escapes the planner
        plan = refused(args, "not-a-repo", str(exc))
    except OSError as exc:
        plan = refused(args, "error", "cannot use the hooks dir: %s"
                       % (exc.strerror or exc), plan)
    except Exception as exc:  # fail closed: never a traceback
        plan = refused(args, "error", "unexpected error: %r" % (exc,), plan)
    return report(plan, args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
