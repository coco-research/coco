"""Apply-side mixin and shared helpers for the Claude Code installer."""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import shutil
import sys
import tempfile
import traceback

DEFAULT_MANAGED = (
    "/Library/Application Support/ClaudeCode/managed-settings.json:"
    "/etc/claude-code/managed-settings.json"
)


class InstallError(Exception):
    """Apply failed. The caller replays the undo stack once."""


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inside(path, root):
    path = os.path.normpath(path)
    root = os.path.normpath(root)
    return path == root or path.startswith(root + os.sep)


class ApplyMixin:
    def fail_if(self, path):
        want = os.environ.get("COCO_INSTALL_FAIL_AT")
        if want and os.path.normpath(want) == os.path.normpath(path):
            raise InstallError("")

    def snapshot(self, path):
        if os.path.islink(path):
            if os.path.isfile(path):
                # open(link, "wb") would follow the link. Record the real file instead.
                real = os.path.realpath(path)
                if not inside(real, self.home_real):
                    self.die("REFUSE: %s resolves outside %s" % (path, self.home))
                with open(real, "rb") as fh:
                    self.undo.append(("bytes", real, fh.read()))
            else:
                self.undo.append(("symlink", path, os.readlink(path)))
        elif os.path.isfile(path):
            with open(path, "rb") as fh:
                self.undo.append(("bytes", path, fh.read()))
        elif not os.path.lexists(path):
            self.undo.append(("rm", path))

    def apply_mkdir(self, path):
        self.fail_if(path)
        self.check_contained(path)
        if self.dry:
            return
        if os.path.isdir(path) and not os.path.islink(path):
            return
        if os.path.lexists(path):
            self.die("REFUSE: %s exists and is not a directory" % path)
        self.undo.append(("rmdir", path))
        os.mkdir(path)

    def apply_link(self, dst, src):
        self.fail_if(dst)
        if self.dry:
            if os.path.islink(dst):
                self.say("DRY: rm %s" % dst)
            self.say("DRY: ln -sf %s %s" % (src, dst))
            self.say("Linked: %s -> %s" % (dst, src))
            return
        if os.path.islink(dst):
            if not self.link_is_ours(dst):
                # Re-checked at apply time: a user link made or repointed after the plan stays.
                self.die("REFUSE: %s became a user link after the plan" % dst)
            self.undo.append(("symlink", dst, os.readlink(dst)))
            os.remove(dst)
        elif os.path.lexists(dst):
            # Appeared after the plan: never record an undo that would delete it.
            self.die("REFUSE: %s appeared after the plan and is not a symlink" % dst)
        else:
            self.undo.append(("rm", dst))
        os.symlink(src, dst)
        self.say("Linked: %s -> %s" % (dst, src))

    def apply_backup(self, src, dest, rec):
        self.fail_if(dest)
        if self.dry:
            return
        if os.path.lexists(dest):
            # A pristine copy is taken once and never overwritten.
            return
        self.undo.append(("rm", dest))
        with open(src, "rb") as fh:
            data = fh.read()
        with open(dest, "wb") as fh:
            fh.write(data)
        digest = hashlib.sha256(data).hexdigest()
        rec["sha256"] = digest
        rec["sha256_after"] = digest

    def apply_generated(self, dest, src, rec):
        self.fail_if(dest)
        if self.dry:
            return
        if os.path.islink(dest):
            self.undo.append(("symlink", dest, os.readlink(dest)))
            os.remove(dest)
        elif os.path.isfile(dest):
            with open(dest, "rb") as fh:
                self.undo.append(("bytes", dest, fh.read()))
        elif os.path.lexists(dest):
            self.die("REFUSE: %s exists and is not a file" % dest)
        else:
            self.undo.append(("rm", dest))
        with open(src, "rb") as fh:
            data = fh.read()
        with open(dest, "wb") as fh:
            fh.write(data)
        digest = hashlib.sha256(data).hexdigest()
        rec["sha256"] = digest
        rec["sha256_after"] = digest
        self.say("Wrote: %s" % dest)

    def apply_block(self, target, block, block_rec, bak_rec, linked_rec=None):
        self.fail_if(target)
        if self.dry:
            self.say("DRY: would write Coco rules block to %s" % target)
            return
        self.snapshot(target)
        self.snapshot(target + ".coco-bak")
        _stdout, stderr = self.run_rules(target, block, plan=False)
        if stderr:
            sys.stderr.write(stderr)
        if _stdout:
            for line in _stdout.splitlines():
                self.say(line)
        if os.path.isfile(target):
            block_rec["sha256_after"] = sha256_file(target)
        if linked_rec is not None and block_rec.get("sha256_after"):
            linked_rec["sha256"] = block_rec["sha256_after"]
            linked_rec["sha256_after"] = block_rec["sha256_after"]
        bak = target + ".coco-bak"
        if bak_rec is not None and os.path.isfile(bak):
            digest = sha256_file(bak)
            bak_rec["sha256"] = digest
            bak_rec["sha256_after"] = digest

    def apply(self, op):
        kind = op[0]
        if kind == "mkdir":
            self.apply_mkdir(op[1])
        elif kind == "link":
            self.apply_link(op[1], op[2])
        elif kind == "skip":
            self.say("Skip: %s (%s)" % (op[1], op[2]))
        elif kind == "stale":
            self.stale_count += 1
            self.say(
                "STALE: %s is a real file or directory, not a symlink — NOT updated. "
                "Remove it to let the installer manage it." % op[1]
            )
        elif kind == "backup":
            self.apply_backup(op[1], op[2], op[3])
        elif kind == "generated":
            self.apply_generated(op[1], op[2], op[3])
        elif kind == "block":
            self.apply_block(*op[1:])
        elif kind == "si_done":
            if not self.dry:
                self.say("Generated %s SI commands into %s" % (op[1], op[2]))
        else:
            self.die("REFUSE: unknown op %s" % kind)

    def warn_stale(self):
        if not self.stale_count:
            return
        self.say("")
        self.say(
            "WARNING: %s target(s) were real files or directories rather than symlinks and were left"
            % self.stale_count
        )
        self.say("untouched. They will keep serving stale content until you remove them. Re-run this")
        self.say("installer afterwards to link them.")

    def body(self):
        counts = {"link": 0, "write": 0, "block": 0, "skip": 0}
        lines = []
        for rec in self.records:
            counts[rec["op"]] += 1
            lines.append(dumps(rec))
        summary = {
            "summary": {
                "adapter": "claude-code",
                "version": self.version,
                "commit": self.commit,
                "target": self.home,
                "link": counts["link"],
                "write": counts["write"],
                "block": counts["block"],
                "skip": counts["skip"],
                "paths": counts["link"] + counts["write"] + counts["block"],
                "managed_settings": self.managed,
            }
        }
        lines.append(dumps(summary))
        return "\n".join(lines) + "\n"

    def finish_manifest(self):
        self.fail_if(self.manifest_path)
        body = self.body()
        parent = os.path.dirname(self.manifest_path)
        fd, tmp = tempfile.mkstemp(prefix=".manifest-", dir=parent)
        self.undo.append(("rm", tmp))
        with os.fdopen(fd, "wb") as fh:
            fh.write(body.encode("utf-8"))
        path = self.manifest_path
        if os.path.islink(path):
            self.undo.append(("symlink", path, os.readlink(path)))
        elif os.path.isfile(path):
            with open(path, "rb") as fh:
                self.undo.append(("bytes", path, fh.read()))
        elif os.path.lexists(path):
            self.die("REFUSE: %s exists and is not a file" % path)
        else:
            self.undo.append(("rm", path))
        os.replace(tmp, path)
        self.undo = []
        return body

    def receipt(self):
        bundles = ",".join(self.bundles) if self.bundles else "core only"
        if self.si_count is not None:
            commands = "%s   (%s core + %s Super Intelligence)" % (
                self.command_count + self.si_count, self.command_count, self.si_count,
            )
        else:
            commands = "%s   (core commands only)" % self.command_count
        self.say("")
        self.say("Installed for Claude Code:")
        self.say("  Slash commands : %s" % commands)
        self.say("  Skills         : %s" % self.skill_count)
        self.say("  Subagents      : %s" % self.agent_count)
        self.say("  Bundles        : %s" % bundles)
        self.say("Core-only install: bash install.sh --adapter claude-code --core-only")

    def replay(self):
        stack = self.undo
        self.undo = []
        for entry in reversed(stack):
            kind = entry[0]
            path = entry[1]
            try:
                if kind == "rm":
                    if os.path.lexists(path) or os.path.islink(path):
                        os.remove(path)
                elif kind == "rmdir":
                    os.rmdir(path)
                elif kind == "symlink":
                    if os.path.lexists(path) or os.path.islink(path):
                        os.remove(path)
                    os.symlink(entry[2], path)
                elif kind == "bytes":
                    with open(path, "wb") as fh:
                        fh.write(entry[2])
            except OSError as exc:
                print("rollback: %s" % exc, file=sys.stderr)

    def execute(self):
        self.applying = True
        try:
            for op in self.ops:
                self.apply(op)
            self.warn_stale()
            if self.dry:
                body = self.body()
            else:
                body = self.finish_manifest()
            if self.json:
                sys.stdout.write(body)
            if not self.dry:
                self.receipt()
            self.say("Done.")
        except (KeyboardInterrupt, SystemExit):
            self.replay()
            raise
        except Exception as exc:
            self.replay()
            if isinstance(exc, (InstallError, OSError)):
                # A refusal or an environment error (disk, permissions): one line is enough.
                if str(exc):
                    print("%s" % exc, file=sys.stderr)
            else:
                # Anything else is a bug: keep its traceback after the rollback.
                traceback.print_exc()
            raise SystemExit(1)

    def detect_managed(self):
        if "COCO_MANAGED_SETTINGS_PATHS" in os.environ:
            raw = os.environ["COCO_MANAGED_SETTINGS_PATHS"]
        else:
            raw = DEFAULT_MANAGED
        for part in raw.split(":"):
            if part and os.path.isfile(part):
                return part
        return None

    def header(self):
        self.managed = self.detect_managed()
        self.say("Coco · Claude Code adapter")
        self.say("Source: %s" % self.repo)
        self.say("Target: %s" % self.home)
        if self.managed:
            self.say("Managed settings: %s" % self.managed)
        else:
            self.say("Managed settings: none")
        if self.dry:
            self.say("(dry-run mode)")

    def acquire_flock(self):
        key = hashlib.sha256(self.home_real.encode("utf-8")).hexdigest()
        path = os.path.join(tempfile.gettempdir(), "coco-install-%s.lock" % key)
        self.lock_fd = open(path, "a+")
        try:
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.lock_fd.close()
            self.lock_fd = None
            if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                self.die("another coco install is running for this target; wait for it to finish")
            raise

    def cleanup(self):
        for staging in self.stagings:
            shutil.rmtree(staging, ignore_errors=True)
        self.stagings = []
        if self.lock_fd is not None:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            self.lock_fd.close()
            self.lock_fd = None

    def run(self):
        try:
            self.header()
            if not self.dry:
                self.acquire_flock()
            self.load_prior()
            self.plan_all()
            self.execute()
        finally:
            self.cleanup()
