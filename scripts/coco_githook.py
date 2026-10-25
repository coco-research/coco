#!/usr/bin/env python3
"""coco-gate githook: put the coco-workflow pre-commit warning into the git hooks
of the repo of the current directory, keep a pre-commit hook that is already
there by chaining it, and never overwrite a file that is not ours.

Python 3.8+ stdlib only. Every message is one line and no traceback escapes;
exit 0 on success, 1 when refused or on error, 2 on a usage error. The only
directory this writes in is the repo's hooks dir, which it asks git for, so a
worktree and core.hooksPath both land in the right place.

  install           write the wrapper, or say it is already there
  install --chain   keep an existing pre-commit hook: it runs after the warning
  remove            take the wrapper out and put the kept hook back
"""

import argparse
import os
import shlex
import subprocess
import sys
import tempfile

MARKER = "# coco-workflow pre-commit wrapper"
CHAINED = "pre-commit.coco-chained"

WRAPPER = """#!/bin/sh
# coco-workflow pre-commit wrapper
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


def say(text):
    """One line per message, whatever the text brought with it."""
    print(" ".join(str(text).split()) or "unknown error")


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


def hooks_dir():
    """The repo's hooks dir, absolute: worktrees and core.hooksPath both apply."""
    try:
        return git("rev-parse", "--path-format=absolute", "--git-path", "hooks")
    except GitError:
        # git before 2.31 has no --path-format, and that spelling is relative to here.
        return os.path.abspath(git("rev-parse", "--git-path", "hooks"))


def coco_hook():
    """The workflow hook the installer links: <claude_home>/coco/hooks/<name>."""
    home = os.environ.get("CLAUDE_HOME") or os.path.expanduser("~/.claude")
    return os.path.abspath(os.path.join(home, "coco", "hooks",
                                        "coco-workflow-pre-commit.sh"))


def is_ours(path):
    """Ours is a regular file, never a symlink, whose second line is the marker."""
    if os.path.islink(path) or not os.path.isfile(path):
        return False
    with open(path, "rb") as fh:
        lines = fh.read().decode("utf-8", "replace").splitlines()
    return len(lines) > 1 and lines[1] == MARKER


def write_wrapper(path, hook, chain):
    """Write the wrapper atomically: a temp file here, chmod, then os.replace."""
    body = WRAPPER % {"hook": shlex.quote(hook), "chain": shlex.quote(chain)}
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".coco-githook.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.chmod(tmp, 0o755)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def cmd_install(args):
    hook = coco_hook()
    if not (os.path.isfile(hook) and os.access(hook, os.X_OK)):
        say("the workflow hooks aren't installed; run the coco installer with "
            "--workflow first")
        return 1
    hooks = hooks_dir()
    os.makedirs(hooks, exist_ok=True)
    target = os.path.join(hooks, "pre-commit")
    chained = os.path.join(hooks, CHAINED)
    if not os.path.lexists(target):
        write_wrapper(target, hook, "")
        say("installed %s" % target)
        return 0
    if is_ours(target):
        say("already installed %s" % target)
        return 0
    if not args.chain:
        say("%s already exists. Re-run with --chain to keep it: it runs after the "
            "warning, and its result decides. Or leave it as it is." % target)
        return 1
    if os.path.lexists(chained):
        say("%s already exists; move it away first" % chained)
        return 1
    os.rename(target, chained)
    try:
        write_wrapper(target, hook, chained)
    except Exception as exc:
        os.rename(chained, target)  # the hook that was here goes back
        say("could not write %s: %s" % (target, exc))
        return 1
    say("installed %s; your hook is now %s, runs after the warning, and its result "
        "decides" % (target, chained))
    return 0


def cmd_remove(args):
    hooks = hooks_dir()
    target = os.path.join(hooks, "pre-commit")
    chained = os.path.join(hooks, CHAINED)
    if not os.path.lexists(target):
        say("nothing to remove")
        return 0
    if not is_ours(target):
        say("%s is not the coco wrapper; leaving it as it is" % target)
        return 1
    os.unlink(target)
    if os.path.lexists(chained):
        os.rename(chained, target)
        say("removed %s; your hook is back in place" % target)
        return 0
    say("removed %s" % target)
    return 0


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
    subs.add_parser("remove", help="take the wrapper out and put your hook back")
    return parser


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 2
    try:
        return {"install": cmd_install, "remove": cmd_remove}[args.cmd](args)
    except GitError as exc:
        say(exc)
        return 1
    except OSError as exc:
        say("cannot use the hooks dir: %s" % (exc.strerror or exc))
        return 1
    except Exception as exc:  # fail closed: never a traceback
        say("unexpected error: %s" % repr(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
