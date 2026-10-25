#!/usr/bin/env python3
"""Undo a Claude Code install from its manifest. Python 3.8+ stdlib.

Manifest lines are untrusted: a path outside the target, or a backup outside
.coco/backup/, is ignored. Output ops are only remove|skip. Dry-run writes nothing.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import traceback

from claude_install import Installer
from claude_install_apply import InstallError, inside, sha256_file


class Uninstaller(Installer):
    def __init__(self, repo, target, dry, as_json):
        super().__init__(repo, target, [], dry, as_json)
        self.summary_ops = ("remove", "skip")
        self.path_ops = ("remove",)
        self.content = []
        self.dir_early = []
        self.dir_late = []
        self.phase3 = []
        self.consumed = set()
        self.gone = set()
        self.owned = set()
        self.backup_paths = set()
    def run(self):
        try:
            self.header()
            self.say("Uninstall")
            if not self.dry:
                self.acquire_flock()
            rows = self.read_manifest()
            if not rows:
                self.nothing()
                return
            self.guard_rows(rows)
            self.decide(rows)
            self.guard_actions()
            self.execute_uninstall()
        finally:
            self.cleanup()
    def nothing(self):
        self.records = []
        self.say("nothing to uninstall (no manifest)")
        if self.json:
            sys.stdout.write(self.body())
        self.say("Done.")
    def home_spell(self, path):
        """Path under self.home, or None. Does not resolve the final component."""
        if not isinstance(path, str) or not path:
            return None
        path = os.path.normpath(path)
        if not os.path.isabs(path):
            return None
        if path == self.home or inside(path, self.home):
            return path
        parent = os.path.dirname(path)
        name = os.path.basename(path)
        if not parent or parent == path:
            return None
        try:
            parent_real = os.path.realpath(parent)
        except OSError:
            return None
        if parent_real != self.home_real and not inside(parent_real, self.home_real):
            return None
        if parent_real == self.home_real:
            spelled = os.path.join(self.home, name) if name else self.home
        else:
            rel = os.path.relpath(parent_real, self.home_real)
            spelled = os.path.normpath(os.path.join(self.home, rel, name))
        if not inside(spelled, self.home):
            return None
        return spelled
    def backup_spell(self, path):
        spelled = self.home_spell(path)
        root = os.path.join(self.home, ".coco", "backup")
        if spelled and spelled.startswith(root + os.sep):
            return spelled
        return None
    def backup_file(self, path):
        spelled = self.backup_spell(path)
        if spelled is None or os.path.islink(spelled) or not os.path.isfile(spelled):
            return False
        root = os.path.join(self.home, ".coco", "backup")
        return inside(os.path.realpath(spelled), os.path.realpath(root))
    def own_sha(self, path):
        if os.path.islink(path) or not os.path.isfile(path):
            return None
        return sha256_file(path)
    def read_regular(self, path):
        if os.path.islink(path) or not os.path.isfile(path):
            return None
        with open(path, "rb") as fh:
            return fh.read()
    def accept(self, raw):
        try:
            line = raw.decode("utf-8").strip()
        except UnicodeDecodeError:
            return None
        if not line:
            return None
        try:
            obj = json.loads(line)
        except ValueError:
            return None
        if not isinstance(obj, dict):
            return None
        op = obj.get("op")
        if op not in ("link", "write", "block", "skip"):
            return None
        path = self.home_spell(obj.get("path"))
        if path is None:
            return None
        backup = obj.get("backup", None)
        if backup is not None:
            if not isinstance(backup, str):
                return None
            backup = self.backup_spell(backup)
            if backup is None:
                return None
        obj = dict(obj)
        obj["path"] = path
        if backup is not None:
            obj["backup"] = backup
        link = obj.get("link_target")
        if isinstance(link, str):
            spelled = self.home_spell(link)
            if spelled is None:
                obj.pop("link_target", None)
            else:
                obj["link_target"] = spelled
        return obj
    def read_manifest(self):
        path = self.manifest_path
        if os.path.islink(path) or not os.path.isfile(path):
            return []
        rows = []
        seen = set()
        with open(path, "rb") as fh:
            for raw in fh:
                rec = self.accept(raw)
                if rec is None or rec["path"] in seen:
                    continue
                seen.add(rec["path"])
                rows.append(rec)
        return rows
    def guard_rows(self, rows):
        for rec in rows:
            self.check_contained(rec["path"])
            backup = rec.get("backup")
            if isinstance(backup, str):
                self.check_contained(backup)
    def guard_actions(self):
        for group in (self.content, self.dir_early, self.phase3, self.dir_late):
            for action in group:
                self.check_contained(action[1])
                if action[0] == "restore":
                    self.check_contained(action[2])
    def emit_remove(self, path, restore=None):
        # restore: "backup" (original bytes back), "link" (old link back) or "block-stripped".
        rec = {"op": "remove", "path": path}
        if restore:
            rec["restore"] = restore
        self.records.append(rec)
    def emit_skip(self, path, reason):
        self.records.append({"op": "skip", "path": path, "reason": reason})
    def note_consumed(self, path):
        if path in self.consumed:
            return
        if os.path.islink(path) or not os.path.isfile(path):
            return
        root = os.path.join(self.home, ".coco", "backup")
        if path.startswith(root + os.sep):
            if not inside(os.path.realpath(path), os.path.realpath(root)):
                return
        elif path not in self.backup_paths:
            return
        self.consumed.add(path)
        self.gone.add(path)
    def consume_block(self, rec, path):
        backup = rec.get("backup")
        if isinstance(backup, str):
            self.note_consumed(backup)
        bak = path + ".coco-bak"
        if bak in self.backup_paths:
            self.note_consumed(bak)
    def preview_strip(self, path):
        data = self.read_regular(path)
        if data is None:
            return None
        fd, tmp = tempfile.mkstemp(prefix="coco-unstrip-")
        os.close(fd)
        try:
            with open(tmp, "wb") as fh:
                fh.write(data)
            rc = self.run_remove(tmp)
            if rc == 3:
                return None
            if rc != 0:
                self.die("write-rules-block.sh exited %s" % rc)
            new = self.read_regular(tmp)
            if new is None or new == data:
                return None
            return new
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
    def run_remove(self, path):
        proc = subprocess.run(
            ["bash", self.rules_script, path, "--remove"],
            input="", capture_output=True, text=True, encoding="utf-8",
        )
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        return proc.returncode
    def decide_link(self, rec):
        path = rec["path"]
        source = rec.get("source")
        if not isinstance(source, str):
            if os.path.lexists(path):
                self.emit_skip(path, "changed since install, kept")
            return
        if os.path.islink(path) and os.readlink(path) == source:
            replaced = rec.get("replaced_link")
            if isinstance(replaced, str) and replaced:
                self.content.append(("relink", path, source, replaced))
                self.emit_remove(path, "link")
            else:
                self.content.append(("delete-link", path, source))
                self.emit_remove(path)
                self.gone.add(path)
            return
        if os.path.lexists(path):
            self.emit_skip(path, "changed since install, kept")
    def decide_generated(self, rec):
        path = rec["path"]
        if path in self.owned:
            return
        digest = rec.get("sha256_after")
        current = self.own_sha(path)
        if not isinstance(digest, str) or current is None:
            if os.path.lexists(path):
                self.emit_skip(path, "changed since install, kept")
            return
        if current != digest:
            self.emit_skip(path, "edited since install, kept")
            return
        backup = rec.get("backup")
        if isinstance(backup, str):
            if not self.backup_file(backup):
                self.emit_skip(path, "changed since install, kept")
                return
            before = self.read_regular(path)
            after = self.read_regular(backup)
            self.content.append(("restore", path, backup, digest))
            if before != after:
                self.emit_remove(path, "backup")
            self.note_consumed(backup)
            return
        self.content.append(("delete-file", path, digest))
        self.emit_remove(path)
        self.gone.add(path)
    def decide_block(self, rec):
        path = rec["path"]
        spelled = rec.get("link_target") if isinstance(rec.get("link_target"), str) else None
        target = spelled or path
        digest = rec.get("sha256_after")
        current = self.own_sha(target)
        if not isinstance(digest, str) or current is None:
            if os.path.lexists(path) or (spelled and os.path.lexists(target)):
                self.emit_skip(target, "changed since install, kept")
            return
        if current == digest:
            if rec.get("created") is True and spelled is None:
                self.content.append(("delete-file", path, digest))
                self.emit_remove(path)
                self.gone.add(path)
                self.consume_block(rec, path)
                return
            backup = rec.get("backup")
            if not isinstance(backup, str) or not self.backup_file(backup):
                self.emit_skip(target, "changed since install, kept")
                return
            before = self.read_regular(target)
            after = self.read_regular(backup)
            self.content.append(("restore", target, backup, digest))
            if before != after:
                self.emit_remove(target, "backup")
            self.consume_block(rec, path)
            return
        if self.preview_strip(target) is None:
            self.emit_skip(target, "edited since install, kept")
            return
        self.content.append(("strip", target, current))
        self.emit_remove(target, "block-stripped")
    def would_be_empty(self, path):
        try:
            names = os.listdir(path)
        except OSError:
            return False
        for name in names:
            child = os.path.normpath(os.path.join(path, name))
            if child not in self.gone:
                return False
        return True
    def is_late(self, path):
        coco = os.path.join(self.home, ".coco")
        return path == self.home or path == coco or inside(path, coco)
    def add_sweep(self, candidates, seen):
        coco = os.path.join(self.home, ".coco")
        backup = os.path.join(coco, "backup")
        extras = []
        if os.path.isdir(coco) and not os.path.islink(coco):
            extras.append(coco)
        if os.path.isdir(backup) and not os.path.islink(backup):
            for dirpath, dirnames, _names in os.walk(backup, followlinks=False):
                extras.append(dirpath)
                dirnames[:] = [
                    name for name in dirnames
                    if not os.path.islink(os.path.join(dirpath, name))
                ]
        for path in extras:
            path = os.path.normpath(path)
            if path not in seen:
                seen.add(path)
                candidates.append(path)
    def decide_dirs(self, dir_recs):
        candidates = []
        seen = set()
        for rec in dir_recs:
            path = rec["path"]
            if path not in seen:
                seen.add(path)
                candidates.append(path)
        self.add_sweep(candidates, seen)
        candidates.sort(key=lambda p: (p.count(os.sep), p), reverse=True)
        for path in candidates:
            if not os.path.lexists(path):
                continue
            if os.path.islink(path) or not os.path.isdir(path):
                self.emit_skip(path, "changed since install, kept")
                continue
            if not self.would_be_empty(path):
                self.emit_skip(path, "not empty, kept")
                continue
            self.gone.add(path)
            self.emit_remove(path)
            bucket = self.dir_late if self.is_late(path) else self.dir_early
            bucket.append(("rmdir", path))
    def decide(self, rows):
        self.records = []
        self.content = []
        self.dir_early = []
        self.dir_late = []
        self.phase3 = []
        self.consumed = set()
        self.gone = set()
        self.owned = set()
        self.backup_paths = set()
        dirs = []
        for rec in rows:
            if rec.get("op") == "write" and rec.get("kind") == "backup":
                self.backup_paths.add(rec["path"])
            if rec.get("op") == "block" and isinstance(rec.get("link_target"), str):
                self.owned.add(rec["link_target"])
        for rec in rows:
            op = rec.get("op")
            if op == "skip":
                reason = rec.get("reason")
                if isinstance(reason, str):
                    self.emit_skip(rec["path"], reason)
            elif op == "link":
                self.decide_link(rec)
            elif op == "block":
                self.decide_block(rec)
            elif op == "write":
                kind = rec.get("kind")
                if kind == "generated":
                    self.decide_generated(rec)
                elif kind == "dir":
                    dirs.append(rec)
        for path in sorted(self.consumed):
            self.emit_remove(path)
            self.phase3.append(("delete-file", path, None))
        if os.path.isfile(self.manifest_path) and not os.path.islink(self.manifest_path):
            self.gone.add(self.manifest_path)
            self.emit_remove(self.manifest_path)
            self.phase3.append(("delete-file", self.manifest_path, None))
        self.decide_dirs(dirs)
    def remember_file(self, path):
        with open(path, "rb") as fh:
            self.undo.append(("bytes", path, fh.read()))
    def do(self, action):
        kind = action[0]
        path = action[1]
        self.fail_if(path)
        self.check_contained(path)
        if self.dry:
            return
        if kind == "delete-link":
            source = action[2]
            if not os.path.islink(path) or os.readlink(path) != source:
                self.die("REFUSE: %s changed during uninstall" % path)
            self.undo.append(("symlink", path, source))
            os.remove(path)
        elif kind == "relink":
            source, replaced = action[2], action[3]
            if not os.path.islink(path) or os.readlink(path) != source:
                self.die("REFUSE: %s changed during uninstall" % path)
            self.undo.append(("symlink", path, source))
            os.remove(path)
            os.symlink(replaced, path)
        elif kind == "delete-file":
            digest = action[2]
            if os.path.islink(path) or not os.path.isfile(path):
                if digest is None and not os.path.lexists(path):
                    return
                self.die("REFUSE: %s changed during uninstall" % path)
            if digest is not None and sha256_file(path) != digest:
                self.die("REFUSE: %s changed during uninstall" % path)
            self.remember_file(path)
            os.remove(path)
        elif kind == "restore":
            backup, digest = action[2], action[3]
            if not self.backup_file(backup) or self.own_sha(path) != digest:
                self.die("REFUSE: %s changed during uninstall" % path)
            self.remember_file(path)
            data = self.read_regular(backup)
            with open(path, "wb") as fh:
                fh.write(data)
            os.chmod(path, os.stat(backup).st_mode & 0o777)
        elif kind == "strip":
            digest = action[2]
            if self.own_sha(path) != digest:
                self.die("REFUSE: %s changed during uninstall" % path)
            self.remember_file(path)
            rc = self.run_remove(path)
            if rc != 0:
                self.die("write-rules-block.sh exited %s" % rc)
        elif kind == "rmdir":
            if os.path.islink(path) or not os.path.isdir(path) or os.listdir(path):
                self.die("REFUSE: %s changed during uninstall" % path)
            self.undo.append(("mkdir", path))
            os.rmdir(path)
        else:
            self.die("REFUSE: unknown uninstall op %s" % kind)
    def execute_uninstall(self):
        self.applying = True
        try:
            for action in self.content:
                self.do(action)
            for action in self.dir_early:
                self.do(action)
            self.fail_if(self.manifest_path)
            if not self.dry:
                for action in self.phase3:
                    self.do(action)
                for action in self.dir_late:
                    self.do(action)
            if self.json:
                sys.stdout.write(self.body())
            self.say("Done.")
        except (KeyboardInterrupt, SystemExit):
            self.replay()
            raise
        except Exception as exc:
            self.replay()
            if isinstance(exc, (InstallError, OSError)):
                if str(exc):
                    print("%s" % exc, file=sys.stderr)
            else:
                traceback.print_exc()
            raise SystemExit(1)
