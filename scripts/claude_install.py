#!/usr/bin/env python3
"""Claude Code install engine. Plan every path, then apply, rolling back on failure.

Python 3.8+ stdlib only. The bash adapter parses flags and chooses bundles;
this process does the plan, the writes, and the manifest.

The exclusive lock is a flock in the system temp dir, named by the sha256 of
realpath(target), so it is not a write inside the target. A pre-existing
TARGET/.coco/install.lock is still a refusal: the safety test plants that
path. This installer never creates it.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

from claude_install_apply import (
    ApplyMixin, COCO_FOOTER, InstallError, dumps, inside, sha256_file,
)

MARKER = "coco:rules"
PROTECTED_BASENAMES = ("settings.json", "settings.local.json", ".credentials.json")
OLD_PARTS = ("skills", "commands", "agents", "systems")
AGENT_SKIP_CORE = ("INDEX.md", "README.md", "PROMPT-DEFENSE.md")
AGENT_SKIP_SYSTEM = ("INDEX.md", "README.md")
# The generator footer is the last thing in the file, so the tail is enough and a
# huge file at a generated path is never read whole.
FOOTER_TAIL = 65536


class Installer(ApplyMixin):
    def __init__(self, repo, target, systems, dry, as_json):
        self.repo = os.path.abspath(repo)
        self.repo_real = os.path.realpath(self.repo)
        self.home = os.path.abspath(target)
        if self.home.endswith(os.sep):
            self.home = self.home.rstrip(os.sep)
        self.home_real = os.path.realpath(self.home)
        self.systems = [s for s in systems if s]
        self.dry = dry
        self.json = as_json
        self.applying = False
        self.records = []
        self.seen_paths = set()
        self.seen_dirs = set()
        self.ops = []
        self.undo = []
        self.stagings = []
        self.lock_fd = None
        self.bundles = []
        self.skill_count = 0
        self.agent_count = 0
        self.command_count = 0
        self.si_count = None
        self.stale_count = 0
        self.carried_count = 0
        self.managed = []
        self.planned_new = set()
        self.prior_created = {}
        self.prior_backup = {}
        self.prior_replaced = {}
        self.prior_kind = {}
        self.prior_sha = {}
        self.prior_records = {}
        self.old_sources = set()
        self.manifest_path = os.path.join(self.home, ".coco", "manifest.jsonl")
        self.summary_ops = ("link", "write", "block", "skip")
        self.path_ops = ("link", "write", "block")
        self.version = self._version()
        self.commit = self._commit()
        self.rules_script = os.path.join(self.repo, "scripts", "write-rules-block.sh")

    def _version(self):
        path = os.path.join(self.repo, "package.json")
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)["version"]

    def _commit(self):
        proc = subprocess.run(
            ["git", "-C", self.repo, "rev-parse", "HEAD"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if proc.returncode != 0:
            return None
        commit = proc.stdout.strip()
        return commit or None

    def say(self, msg):
        print(msg, file=sys.stderr if self.json else sys.stdout)

    def die(self, msg):
        if self.applying:
            raise InstallError(msg)
        if msg:
            print(msg, file=sys.stderr)
        raise SystemExit(1)

    def refuse_protected(self, path):
        base = os.path.basename(path)
        if base in PROTECTED_BASENAMES and os.path.dirname(path) == self.home:
            self.die("REFUSE: %s is protected and will not be modified" % path)
        projects = os.path.join(self.home, "projects")
        if path == projects or path.startswith(projects + os.sep):
            self.die("REFUSE: %s is protected and will not be modified" % path)

    def check_contained(self, path):
        """Parent realpath must stay inside the target. The target's own parent may not."""
        path = os.path.normpath(os.path.abspath(path))
        if not inside(path, self.home):
            self.die("REFUSE: target %s is outside %s" % (path, self.home))
        self.refuse_protected(path)
        if path == self.home:
            return path
        cur = os.path.dirname(path)
        while cur != self.home and not os.path.lexists(cur):
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
        if not os.path.lexists(cur):
            return path
        real = os.path.realpath(cur)
        if not inside(real, self.home_real):
            self.die("REFUSE: %s leaves %s through %s" % (path, self.home, cur))
        return path

    def add_record(self, rec):
        path = rec["path"]
        if path in self.seen_paths:
            self.die("REFUSE: duplicate plan path %s" % path)
        self.seen_paths.add(path)
        self.records.append(rec)
        return rec

    def add_write(self, path, kind, backup=None, carry=True):
        path = self.check_contained(path)
        if carry and not backup:
            backup = self.prior_backup.get(path) or None
        rec = {
            "op": "write",
            "path": path,
            "kind": kind,
            "sha256": None,
            "sha256_after": None,
        }
        if backup:
            rec["backup"] = backup
        return self.add_record(rec)

    def add_link(self, dst, src, replaced):
        if not replaced:
            replaced = self.prior_replaced.get(dst) or ""
        rec = {"op": "link", "path": dst, "source": src}
        if replaced:
            rec["replaced_link"] = replaced
        return self.add_record(rec)

    def add_block(self, path, backup, created, link_target=None):
        path = self.check_contained(path)
        if not created and self.prior_created.get(path) is True:
            created = True
        if not backup:
            backup = self.prior_backup.get(path) or None
        rec = {
            "op": "block",
            "path": path,
            "marker": MARKER,
            "backup": backup,
            "created": bool(created),
            "sha256_after": None,
        }
        # null, not omitted: uninstall keeps the symlink and restores bytes only.
        if link_target:
            rec["replaced_link"] = None
            rec["link_target"] = link_target
        return self.add_record(rec)

    def add_skip(self, path, reason):
        path = self.check_contained(path)
        return self.add_record({"op": "skip", "path": path, "reason": reason})

    def note_dir(self, path):
        path = self.check_contained(path)
        if os.path.isdir(path):
            if self.prior_kind.get(path) == "dir" and path not in self.seen_dirs:
                self.seen_dirs.add(path)
                self.add_write(path, "dir", carry=False)
            else:
                self.seen_dirs.add(path)
            return
        if path in self.seen_dirs:
            return
        if os.path.lexists(path):
            self.die("REFUSE: %s exists and is not a directory" % path)
        self.seen_dirs.add(path)
        self.add_write(path, "dir", carry=False)
        self.ops.append(("mkdir", path))

    def ensure_dir(self, dest):
        dest = self.check_contained(dest)
        cur = self.home
        self.note_dir(cur)
        if dest != self.home:
            rel = dest[len(self.home) + 1:]
            for part in rel.split(os.sep):
                if not part:
                    continue
                cur = os.path.join(cur, part)
                self.note_dir(cur)

    def child_dirs(self, path):
        if not os.path.isdir(path):
            return []
        names = []
        for name in sorted(os.listdir(path)):
            if name.startswith("."):
                continue
            if os.path.isdir(os.path.join(path, name)):
                names.append(name)
        return names

    def child_md(self, path):
        if not os.path.isdir(path):
            return []
        names = []
        for name in sorted(os.listdir(path)):
            if name.startswith(".") or not name.endswith(".md"):
                continue
            if os.path.isfile(os.path.join(path, name)):
                names.append(name)
        return names

    def link_text(self, dst):
        raw = os.readlink(dst)
        if os.path.isabs(raw):
            return raw, os.path.normpath(raw)
        abs_text = os.path.normpath(os.path.join(os.path.dirname(dst), raw))
        return raw, abs_text

    def consider_old_source(self, source):
        if not isinstance(source, str) or not source:
            return
        norm = os.path.normpath(source)
        if not os.path.isabs(norm) or inside(norm, self.home):
            return
        parts = norm.split(os.sep)
        if not any(part in OLD_PARTS and i >= 2 for i, part in enumerate(parts)):
            return
        self.old_sources.add(norm)

    def link_is_ours(self, dst):
        _raw, abs_text = self.link_text(dst)
        real = os.path.realpath(abs_text)
        if inside(abs_text, self.repo) or inside(abs_text, self.repo_real):
            return True
        if inside(real, self.repo) or inside(real, self.repo_real):
            return True
        abs_norm = os.path.normpath(abs_text)
        for src in self.old_sources:
            if abs_norm == src or real == os.path.realpath(src):
                return True
        return False

    def replaced_of(self, dst, src):
        if not os.path.islink(dst):
            return ""
        old = os.readlink(dst)
        if old == src:
            return ""
        try:
            if os.path.realpath(dst) == os.path.realpath(src):
                return ""
        except OSError:
            pass
        return old

    def plan_link(self, src, dst, count=None):
        dst = self.check_contained(dst)
        if os.path.islink(dst) and not self.link_is_ours(dst):
            self.add_skip(dst, "user link, not replaced")
            self.ops.append(("skip", dst, "user link, not replaced"))
        elif os.path.lexists(dst) and not os.path.islink(dst):
            self.add_skip(dst, "user file, not overwritten")
            self.ops.append(("stale", dst))
        else:
            replaced = self.replaced_of(dst, src)
            parent = os.path.dirname(dst)
            if parent:
                self.ensure_dir(parent)
            self.add_link(dst, src, replaced)
            self.ops.append(("link", dst, src))
        if count == "skill" and os.path.isfile(os.path.join(src.rstrip(os.sep), "SKILL.md")):
            self.skill_count += 1
        elif count == "skill-always":
            self.skill_count += 1
        elif count == "command":
            self.command_count += 1
        elif count == "agent":
            self.agent_count += 1

    def prior_unchanged(self, path):
        sha = self.prior_sha.get(path) or ""
        if not sha or os.path.islink(path) or not os.path.isfile(path):
            return False
        return sha256_file(path) == sha

    def coco_owned(self, path):
        """True when a file at a generated path still carries the coco footer line."""
        try:
            size = os.path.getsize(path)
            with open(path, "rb") as fh:
                if size > FOOTER_TAIL:
                    fh.seek(size - FOOTER_TAIL)
                return COCO_FOOTER in fh.read()
        except OSError:
            return False

    def stage_backup(self, path, source=None):
        """Pristine copy once. A symlink records no content unless source is the resolved file."""
        src = path if source is None else source
        if source is None:
            if os.path.islink(path) or not os.path.isfile(path):
                return None
        elif (
            os.path.islink(src)
            or not os.path.isfile(src)
            or not inside(os.path.realpath(src), self.home_real)
        ):
            return None
        rel = os.path.relpath(path, self.home)
        dest = self.check_contained(os.path.join(self.home, ".coco", "backup", rel))
        if os.path.lexists(dest):
            return dest
        self.ensure_dir(os.path.dirname(dest))
        rec = self.add_write(dest, "backup", carry=False)
        self.ops.append(("backup", src, dest, rec))
        return dest

    def load_prior(self):
        path = self.manifest_path
        if not os.path.isfile(path) or os.path.islink(path):
            return
        home = os.path.normpath(self.home)
        backup_root = os.path.normpath(os.path.join(home, ".coco", "backup"))
        seen = set()
        with open(path, "rb") as fh:
            for raw in fh:
                try:
                    line = raw.decode("utf-8").strip()
                except UnicodeDecodeError:
                    continue
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                rec_path = obj.get("path")
                if not isinstance(rec_path, str):
                    continue
                rec_path = os.path.normpath(rec_path)
                if not os.path.isabs(rec_path) or not inside(rec_path, home):
                    continue
                if rec_path in seen:
                    continue
                seen.add(rec_path)
                self.prior_records[rec_path] = obj
                created = obj.get("created")
                if created is True or created is False:
                    self.prior_created[rec_path] = created
                backup = obj.get("backup")
                if isinstance(backup, str):
                    bnorm = os.path.normpath(backup)
                    if os.path.isabs(bnorm) and bnorm.startswith(backup_root + os.sep):
                        self.prior_backup[rec_path] = bnorm
                replaced = obj.get("replaced_link")
                if isinstance(replaced, str):
                    self.prior_replaced[rec_path] = replaced
                op = obj.get("op")
                if op == "write":
                    kind = obj.get("kind")
                    if isinstance(kind, str):
                        self.prior_kind[rec_path] = kind
                    digest = obj.get("sha256_after")
                    if not isinstance(digest, str):
                        digest = obj.get("sha256")
                    if isinstance(digest, str):
                        self.prior_sha[rec_path] = digest
                elif op == "block":
                    digest = obj.get("sha256_after")
                    if isinstance(digest, str):
                        self.prior_sha[rec_path] = digest
                elif op == "link":
                    self.consider_old_source(obj.get("source"))

    def rules_block(self):
        rules_dir = os.path.join(self.repo, "rules", "cursor-mdc")
        names = []
        if os.path.isdir(rules_dir):
            for name in sorted(os.listdir(rules_dir)):
                if name.startswith(".") or not name.endswith(".mdc"):
                    continue
                if os.path.isfile(os.path.join(rules_dir, name)):
                    names.append(name[:-4])
        lines = [
            "<!-- coco:rules-start -->",
            "<!-- This block is auto-generated by adapters/claude-code/install.sh.",
            "     Edit the source files in %s/rules/ — re-run install to refresh. -->" % self.repo,
            "",
            "# Coco — cross-IDE rules",
            "",
            "The following rules apply globally. Source: `%s/rules/cursor-mdc/`" % self.repo,
        ]
        for name in names:
            lines.append("- `%s`" % name)
        lines.append("")
        lines.append(
            "For each rule, see [`rules/cursor-mdc/`](%s/rules/cursor-mdc/)." % self.repo
        )
        lines.append("")
        lines.append("<!-- coco:rules-end -->")
        return "\n".join(lines)

    def run_rules(self, target, block, plan):
        cmd = ["bash", self.rules_script, target]
        if plan:
            cmd.append("--plan")
        proc = subprocess.run(
            cmd, input=block + "\n", capture_output=True, text=True, encoding="utf-8",
        )
        if proc.returncode != 0:
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            if proc.stdout:
                sys.stderr.write(proc.stdout)
            self.die("write-rules-block.sh exited %s" % proc.returncode)
        return proc.stdout, proc.stderr

    def skip_rules(self, path, reason):
        rec = self.add_skip(path, reason)
        self.ops.append(("skip", rec["path"], reason))

    def plan_rules(self):
        target = os.path.join(self.home, "CLAUDE.md")
        self.ensure_dir(self.home)
        # link_real is the resolved file spelled under self.home. realpath(/var) is
        # /private/var on macOS, which check_contained and the path compare refuse.
        link_real = None
        link_target = None
        if os.path.islink(target):
            # Dangling before outside: realpath of a missing link is not a file we can trust.
            if not os.path.exists(target):
                self.skip_rules(target, "CLAUDE.md is a dangling link; rules block not added")
                return
            real = os.path.realpath(target)
            if not inside(real, self.home_real):
                self.skip_rules(target, "CLAUDE.md links outside the target; rules block not added")
                return
            if os.path.isfile(real):
                link_target = real
                link_real = os.path.normpath(os.path.join(
                    self.home, os.path.relpath(real, self.home_real)))
        block = self.rules_block()
        stdout, stderr = self.run_rules(target, block, plan=True)
        if stderr:
            sys.stderr.write(stderr)
        plan_out = stdout.strip()
        existed = os.path.lexists(target)
        block_backup = None
        pristine = os.path.join(self.home, ".coco", "backup", "CLAUDE.md")
        if existed and plan_out:
            block_backup = self.stage_backup(target, link_real)
        elif os.path.lexists(pristine):
            block_backup = pristine
        bak_rec = None
        if plan_out:
            bak_path = self.check_contained(plan_out)
            bak_rec = self.add_write(bak_path, "backup", carry=False)
        block_rec = self.add_block(target, block_backup, not existed, link_target)
        # Symlink entry is unchanged; the resolved file's bytes change. List it or the
        # path compare reports an unplanned write.
        linked_rec = None
        if link_real and plan_out and link_real != os.path.normpath(target):
            linked_rec = self.add_write(link_real, "generated", carry=False)
        self.ops.append(("block", target, block, block_rec, bak_rec, linked_rec))

    def team_name(self, skill_md, fallback):
        try:
            with open(skill_md, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.startswith("name:"):
                        name = line[len("name:"):].lstrip(" ").rstrip("\r\n").replace('"', "")
                        return name or fallback
        except OSError:
            pass
        return fallback

    def run_generator(self, script, staging):
        env = os.environ.copy()
        env["COCO_SI_COMMANDS_DIR"] = staging
        # Claude Code expands $ARGUMENTS. The generators keep {{ARGUMENTS}} unless told.
        env["COCO_SI_ARGUMENTS"] = "$ARGUMENTS"
        proc = subprocess.run(
            [sys.executable, script],
            cwd=self.repo, env=env,
            capture_output=True, text=True, encoding="utf-8",
        )
        if proc.returncode != 0:
            if proc.stdout:
                sys.stderr.write(proc.stdout if proc.stdout.endswith("\n") else proc.stdout + "\n")
            if proc.stderr:
                sys.stderr.write(proc.stderr if proc.stderr.endswith("\n") else proc.stderr + "\n")
            raise SystemExit(1)
        if proc.stderr:
            sys.stderr.write(proc.stderr if proc.stderr.endswith("\n") else proc.stderr + "\n")

    def plan_si(self, sys_dir):
        script = os.path.join(sys_dir, "ai", "scripts", "build_commands.py")
        meta = os.path.join(sys_dir, "scripts", "build_meta_commands.py")
        if not os.path.isfile(script):
            return
        if not os.path.isfile(meta):
            self.die("SI generator missing: %s" % meta)
        staging = tempfile.mkdtemp(prefix="coco-si-")
        self.stagings.append(staging)
        self.run_generator(script, staging)
        self.run_generator(meta, staging)
        files = []
        for dirpath, dirnames, filenames in os.walk(staging):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for name in filenames:
                if name.startswith("."):
                    continue
                src = os.path.join(dirpath, name)
                if os.path.islink(src) or not os.path.isfile(src):
                    continue
                rel = os.path.relpath(src, staging)
                files.append((rel, src))
        files.sort()
        commands = os.path.join(self.home, "commands")
        written = 0
        for rel, src in files:
            dest = self.check_contained(os.path.normpath(os.path.join(commands, rel)))
            if os.path.islink(dest) and not self.link_is_ours(dest):
                self.add_skip(dest, "user link, not replaced")
                self.ops.append(("skip", dest, "user link, not replaced"))
                continue
            if os.path.lexists(dest) and not os.path.islink(dest) and not os.path.isfile(dest):
                self.add_skip(dest, "user file, not overwritten")
                self.ops.append(("stale", dest))
                continue
            owned = False
            backup = None
            if os.path.isfile(dest) and not os.path.islink(dest):
                # A regular file here is coco's own only when the previous plan wrote it
                # or it still carries the generator footer. Anything else is the user's.
                owned = self.prior_kind.get(dest) == "generated" or self.coco_owned(dest)
                if not owned:
                    self.add_skip(dest, "user file, not overwritten")
                    self.ops.append(("skip", dest, "user file, not overwritten"))
                    continue
                if self.prior_unchanged(dest):
                    backup = self.prior_backup.get(dest) or None
                else:
                    backup = self.stage_backup(dest)
            else:
                self.ensure_dir(os.path.dirname(dest))
                self.planned_new.add(dest)
            rec = self.add_write(dest, "generated", backup=backup, carry=False)
            if owned:
                rec["replaces"] = "previous coco file"
            self.ops.append(("generated", dest, src, rec))
            written += 1
        self.ops.append(("si_done", written, commands))
        self.si_count = (self.si_count or 0) + written

    def plan_skills(self, directory, prefix, count):
        if not os.path.isdir(directory):
            return
        for name in self.child_dirs(directory):
            src = os.path.join(directory, name) + os.sep
            dst = os.path.join(self.home, prefix, name)
            self.plan_link(src, dst, count=count)

    def plan_md_files(self, directory, dest_dir, count, skip_names):
        if not os.path.isdir(directory):
            return
        for name in self.child_md(directory):
            src = os.path.join(directory, name)
            dst = os.path.join(dest_dir, name)
            self.plan_link(src, dst, count=None if name in skip_names else count)

    def plan_core(self):
        self.plan_skills(os.path.join(self.repo, "skills"), "skills", "skill")
        commands = os.path.join(self.repo, "commands")
        for nsname in self.child_dirs(commands):
            ns = os.path.join(commands, nsname)
            for fname in self.child_md(ns):
                src = os.path.join(ns, fname)
                cname = fname[:-3]
                if cname == "_index":
                    dst = os.path.join(self.home, "commands", nsname + ".md")
                else:
                    dst = os.path.join(self.home, "commands", "%s:%s.md" % (nsname, cname))
                self.plan_link(src, dst, count="command")
        self.plan_md_files(
            os.path.join(self.repo, "agents"),
            os.path.join(self.home, "agents"),
            "agent",
            AGENT_SKIP_CORE,
        )
        self.plan_rules()

    def plan_system(self, sys):
        sys_dir = os.path.join(self.repo, "systems", sys)
        if not os.path.isdir(sys_dir):
            self.die("Unknown system: %s" % sys)
        self.bundles.append(sys)
        self.plan_skills(os.path.join(sys_dir, "skills"), "skills", "skill-always")
        for name in self.child_dirs(sys_dir):
            team = os.path.join(sys_dir, name)
            skill_md = os.path.join(team, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue
            link_name = self.team_name(skill_md, name)
            self.plan_link(team + os.sep, os.path.join(self.home, "skills", link_name), count="skill-always")
        self.plan_md_files(
            os.path.join(sys_dir, "agents"),
            os.path.join(self.home, "agents"),
            "agent",
            AGENT_SKIP_SYSTEM,
        )
        self.plan_md_files(
            os.path.join(sys_dir, "commands"),
            os.path.join(self.home, "commands"),
            "command",
            (),
        )
        self.plan_si(sys_dir)

    def plan_manifest(self):
        self.ensure_dir(os.path.join(self.home, ".coco"))
        self.add_write(self.manifest_path, "manifest", carry=False)

    def plan_carry(self):
        # Rows an earlier install wrote and this selection no longer plans stay in the
        # manifest, so --uninstall still undoes them.
        # ponytail: carry never prunes, so a narrower selection does not shrink what is
        # installed. The upgrade path is an explicit --prune flag, if users ask for one.
        for path, row in self.prior_records.items():
            op = row.get("op")
            if op not in self.path_ops:
                continue
            if path in self.seen_paths or not os.path.lexists(path):
                continue
            if op == "link":
                if not os.path.islink(path) or not self.link_is_ours(path):
                    continue
            elif op == "write":
                if row.get("kind") == "dir":
                    if os.path.islink(path) or not os.path.isdir(path):
                        continue
                elif os.path.islink(path) or not os.path.isfile(path):
                    continue
            elif os.path.islink(path) or not os.path.isfile(path):
                continue
            self.add_record(dict(row, carried=True))
            self.carried_count += 1

    def plan_all(self):
        self.plan_core()
        for sys in self.systems:
            self.plan_system(sys)
        self.plan_manifest()
        self.plan_carry()


def main(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--system", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args(argv)
    if args.uninstall:
        from claude_uninstall import Uninstaller
        Uninstaller(args.repo, args.target, args.dry_run, args.json).run()
        return
    Installer(args.repo, args.target, args.system, args.dry_run, args.json).run()


if __name__ == "__main__":
    main(sys.argv[1:])
