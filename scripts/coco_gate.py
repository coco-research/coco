#!/usr/bin/env python3
"""coco-gate: the `coco-workflow` required check.

Feature work goes PRD -> architecture -> plan, each stage signed by a named
person or agent role; this verifies those sign-offs are real, current and
signed by the right role. Local hooks only nudge. This is the lock.

  init   --branch B --size feature|small --builder ID [--prd P --arch P --plan P] [--ui GLOB ...]
  sign   --stage prd|arch|plan|mock|approve|size|infra --signer ID --key KEY [--artifact P]
         [--decision P] [--base REF] [--base-commit SHA]
  verify [--ci --base REF] [--signers FILE] [--policy FILE] [--branch B] [--changed FILE]
         [--changed-numstat FILE]
  status [--branch B]

In CI the signers, the policy and this verifier come from the base branch, so a
PR cannot add a key, loosen the policy or edit this file and benefit in the same
PR. Outside --ci everything comes from the work tree: a local preview, and the
ok line says so.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

GATE_DIR = ".coco/gates"
SIGNERS_PATH = ".coco/allowed_signers"
POLICY_PATH = ".coco/workflow.json"
NAMESPACE = "coco-gate"
CHAIN = ("prd", "arch", "plan")
STAGES = ("prd", "arch", "plan", "mock", "approve", "size", "infra")
MESSAGE_KEYS = ("repo", "branch", "base", "stage", "size", "artifact", "sha256",
                "prev", "decision", "signer", "at")
POLICY_STAGE = {"size": "arch", "infra": "arch"}
TIMEOUT = 60
KEYTYPE = re.compile(r"^(ssh-|ecdsa-|sk-)")
DEFAULT_POLICY = {
    "feature_branches": ["feat/*"],
    "stages": {"prd": ["brain"], "arch": ["steve", "council"],
               "plan": ["steve", "council"], "mock": ["design"],
               "approve": ["steve"]},
    "no_sign_roles": ["factory"],
    "approver_key": "relay",
    "small_max_lines": 300,
    "protected": [".githooks/**", "hooks/coco-*", ".github/workflows/**",
                  ".coco/allowed_signers", ".coco/workflow.json", "scripts/coco_gate.py"],
}


class GateError(Exception):
    """One line, no traceback: a fail-closed result."""


def need(ok, message):
    """One failure line per broken rule, and never a traceback."""
    if not ok:
        raise GateError(message)


def one_line(text):
    return " ".join(str(text).split()) or "unknown error"


def say(text):
    print("coco-workflow: " + one_line(text))


def sha_hex(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    with open(path, "rb") as fh:
        return sha_hex(fh.read())


def safe_rel(path):
    """True for a repo-relative path that cannot escape the repo."""
    if not isinstance(path, str) or not path.strip():
        return False
    name = path.replace("\\", "/")
    if name.startswith("/") or re.match(r"^[A-Za-z]:/", name):
        return False
    return ".." not in name.split("/")


def glob_match(path, pattern):
    """fnmatch, but `*` stays in one segment so `web/*` is not `web/**`."""
    if "**" not in pattern:
        return fnmatch.fnmatch(path, pattern)
    pieces = re.split(r"(\*\*|\*|\?)", pattern)
    regex = "".join(".*" if p == "**" else "[^/]*" if p == "*"
                    else "[^/]" if p == "?" else re.escape(p) for p in pieces)
    return re.fullmatch(regex, path) is not None


def gate_path(branch):
    return GATE_DIR + "/" + branch.replace("/", "__") + ".json"


def prev_stage(stage):
    return {"arch": "prd", "plan": "arch"}.get(stage, "")


def latest(gate, stage):
    entries = [e for e in gate.get("signoffs", [])
               if isinstance(e, dict) and e.get("stage") == stage]
    return sorted(entries, key=lambda e: str(e.get("at", "")), reverse=True)[0] \
        if entries else None


def git(args):
    argv = ["git"] + list(args)
    try:
        proc = subprocess.run(argv, stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        raise GateError("timeout after %ds: %s" % (TIMEOUT, " ".join(argv)))
    except OSError as exc:
        return 127, b"", one_line(exc).encode("utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def git_text(args):
    code, out, _err = git(args)
    return out.decode("utf-8", "replace") if code == 0 else None


def is_ancestor(commit, ref):
    return git(["merge-base", "--is-ancestor", commit, ref])[0] == 0


def merge_base(base):
    out = (git_text(["merge-base", "HEAD", "origin/" + base])
           or git_text(["merge-base", "HEAD", base]) or "").strip()
    need(re.match(r"^[0-9a-f]{40}$", out),
         "cannot find the merge-base with %s; pass --base-commit" % base)
    return out


def protected_hits(text, policy):
    return sorted({p.strip() for p in text.splitlines() if p.strip()
                   and any(glob_match(p.strip(), g) for g in policy["protected"])})


def infra_hex(paths):
    lines = sorted("%s %s\n" % (p, (git_text(["rev-parse", "HEAD:" + p])
                                    or "deleted").strip()) for p in paths)
    return sha_hex("".join(lines).encode("utf-8"))


def normalise_repo(url):
    name = (url or "").strip().rstrip("/")
    name = name[:-4] if name.endswith(".git") else name
    tail = re.sub(r"^[^/:]+:", "", re.sub(r"^[a-z]+://[^/]+/", "", name))
    parts = [p for p in tail.strip("/").split("/") if p]
    return "/".join(parts[-2:]) if len(parts) >= 2 else "".join(parts)


def repo_slug():
    for var in ("COCO_GATE_REPO", "GITHUB_REPOSITORY"):
        value = os.environ.get(var, "").strip()
        if value:
            return normalise_repo(value)
    url = git_text(["remote", "get-url", "origin"])
    need(url, "cannot read the origin remote; set COCO_GATE_REPO")
    slug = normalise_repo(url)
    need(slug, "cannot normalise the origin remote: %s" % one_line(url))
    return slug


def current_branch():
    name = (git_text(["rev-parse", "--abbrev-ref", "HEAD"]) or "").strip()
    need(name, "cannot read the current git branch")
    return name


def read_text(path, what=None):
    """Read a file. With no `what`, a missing file is None; with it, a fail."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (IOError, OSError) as exc:
        if what is None:
            return None
        raise GateError("cannot read %s %s: %s" % (what, path, one_line(exc)))


def write_file(path, data):
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def parse_json(text, what):
    try:
        return json.loads(text)
    except ValueError as exc:
        raise GateError("%s: malformed JSON (%s)" % (what, one_line(exc)))


def write_json(path, obj):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")


def canonical(entry):
    """The signed bytes: exactly these lines, each ending in a newline."""
    lines = ["coco-gate/1"]
    for key in MESSAGE_KEYS:
        value = entry.get(key, "")
        lines.append("%s=%s" % (key, "" if value is None else value))
    return "\n".join(lines) + "\n"


def parse_signers(text):
    """principal -> (role, keytype) from an OpenSSH allowed_signers file."""
    roles = {}
    for raw in text.splitlines():
        line = raw.strip()
        found = re.search(r"coco-role=([A-Za-z0-9_.\-]+)", line)
        if not line or line.startswith("#") or not found:
            continue
        try:
            tokens = shlex.split(line)
        except ValueError:
            continue
        index = next((i for i in range(1, len(tokens)) if KEYTYPE.match(tokens[i])), None)
        if index is None or index >= len(tokens) - 1:
            continue
        for principal in tokens[0].split(","):
            roles.setdefault(principal.strip(), (found.group(1), tokens[index]))
    return roles


def load_policy(text, source):
    if text is None:
        return json.loads(json.dumps(DEFAULT_POLICY))
    data = parse_json(text, source)
    need(isinstance(data, dict), "%s: policy is not a JSON object" % source)
    policy = json.loads(json.dumps(DEFAULT_POLICY))
    policy.update(data)
    for key in ("feature_branches", "no_sign_roles", "protected"):
        value = policy.get(key)
        need(isinstance(value, list) and all(isinstance(x, str) for x in value),
             "%s: %s must be a list of strings" % (source, key))
    stages = policy.get("stages")
    need(isinstance(stages, dict) and all(
        isinstance(v, list) and all(isinstance(x, str) for x in v) for v in stages.values()),
        "%s: stages must map stage names to role lists" % source)
    need(policy.get("approver_key") in ("relay", "sk"),
         "%s: approver_key must be relay or sk" % source)
    limit = policy.get("small_max_lines")
    need(isinstance(limit, int) and not isinstance(limit, bool) and limit > 0,
         "%s: small_max_lines must be a positive integer" % source)
    return policy


def check_gate(gate, path):
    need(isinstance(gate, dict), "%s: gate file is not a JSON object" % path)
    need(gate.get("schema") == 1, "%s: unsupported schema %r" % (path, gate.get("schema")))
    for key in ("repo", "branch", "size", "builder"):
        need(isinstance(gate.get(key), str) and gate.get(key),
             "%s: missing or empty %s" % (path, key))
    need(gate["size"] in ("feature", "small"), "%s: size must be feature or small" % path)
    artifacts = gate.get("artifacts") or {}
    need(isinstance(artifacts, dict), "%s: artifacts must be an object" % path)
    for stage in CHAIN:
        if artifacts.get(stage) is None and gate["size"] == "small":
            continue
        need(safe_rel(artifacts.get(stage)),
             "%s: artifacts.%s is not a repo-relative path: %s"
             % (path, stage, artifacts.get(stage)))
    ui = gate.get("ui", [])
    need(isinstance(ui, list) and all(isinstance(x, str) for x in ui),
         "%s: ui must be a list of globs" % path)
    signoffs = gate.get("signoffs", [])
    need(isinstance(signoffs, list), "%s: signoffs must be a list" % path)
    for entry in signoffs:
        need(isinstance(entry, dict) and isinstance(entry.get("sig"), str),
             "%s: a sign-off is not an object with a string sig" % path)
    return gate


def run_ssh(argv, data=None):
    """ssh-keygen with an explicit stdin policy and a timeout, or one FAIL line."""
    try:
        return subprocess.run(["ssh-keygen"] + argv, input=data,
                              stdin=None if data is not None else subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        raise GateError("timeout after %ds: ssh-keygen %s"
                        % (TIMEOUT, " ".join(argv[:2])))
    except OSError as exc:
        raise GateError("cannot run ssh-keygen: %s" % one_line(exc))


def check_ssh():
    need(shutil.which("ssh-keygen"), "ssh-keygen not found on PATH")
    probe = os.path.join(tempfile.gettempdir(), "coco-gate-probe-no-such-key")
    proc = run_ssh(["-Y", "sign", "-f", probe, "-n", NAMESPACE, "-"])
    blob = (proc.stdout + proc.stderr).decode("utf-8", "replace").lower()
    need(not any("%s option" % word in blob
                 for word in ("unknown", "illegal", "invalid")),
         "ssh-keygen lacks -Y support (need OpenSSH 8.1 or newer)")


def ssh_sign(key, message):
    # T7 (lab-0514): coco-gate never opens a private key file. It takes the public
    # key and ssh-keygen asks ssh-agent to sign with the matching private key.
    need(key.endswith(".pub"),
         "--key takes a public key (.pub); signing goes through ssh-agent and coco-gate never opens a private key")
    need(os.environ.get("SSH_AUTH_SOCK"), "SSH_AUTH_SOCK is unset; load the key into ssh-agent first")
    work = tempfile.mkdtemp(prefix="coco-sign-")
    try:
        msg = write_file(os.path.join(work, "message"), message.encode("utf-8"))
        proc = run_ssh(["-Y", "sign", "-f", key, "-n", NAMESPACE, msg])
        sig = msg + ".sig"
        if proc.returncode != 0 or not os.path.exists(sig):
            detail = proc.stderr.decode("utf-8", "replace") or "exit %d" % proc.returncode
            raise GateError("ssh-keygen sign failed: %s" % one_line(detail))
        return read_text(sig, "signature")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def ssh_verify(signers_file, signer, message, signature):
    work = tempfile.mkdtemp(prefix="coco-verify-")
    try:
        sig = write_file(os.path.join(work, "signature"), signature.encode("utf-8"))
        proc = run_ssh(["-Y", "verify", "-f", signers_file, "-I", signer,
                        "-n", NAMESPACE, "-s", sig], message.encode("utf-8"))
        return proc.returncode == 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


class Check(object):
    def __init__(self, args):
        self.args = args
        self.ci = bool(args.ci)
        self.base = args.base or os.environ.get("GITHUB_BASE_REF", "") or "main"
        self.base_ref = ("origin/" + self.base) if self.ci else self.base
        self.branch = (args.branch or os.environ.get("GITHUB_HEAD_REF", "")
                       or current_branch())
        self.repo = repo_slug()
        self.path = gate_path(self.branch)
        self.policy = self.roles = self.signers_file = self.gate = None
        self.tmp = None
        self.fails, self.notes = [], []

    def fail(self, reason, stage=None):
        self.fails.append("%s: %s" % (stage, reason) if stage else reason)

    def finish(self):
        for note in self.notes:
            say(note)
        for item in self.fails:
            say("FAIL " + item)
        if self.fails:
            say("FAIL %d finding(s) on %s" % (len(self.fails), self.branch))
            return 1
        where = ("signers and policy from %s" % self.base_ref) if self.ci else \
            "local preview: signers and policy from the work tree, not the base branch"
        say("ok %s on %s (%s)" % (self.path if self.gate else "no gate", self.branch, where))
        return 0

    def load_policy(self):
        if self.args.policy:
            return load_policy(read_text(self.args.policy, "policy file"), self.args.policy)
        source = "%s:%s" % (self.base_ref, POLICY_PATH) if self.ci else POLICY_PATH
        text = git_text(["show", source]) if self.ci else read_text(POLICY_PATH)
        return load_policy(text, source)

    def load_signers(self):
        source = self.args.signers or SIGNERS_PATH
        if self.ci and not self.args.signers:
            source = "%s:%s" % (self.base_ref, SIGNERS_PATH)
            text = git_text(["show", source])
            need(text is not None,
                 "cannot read %s; the base branch owns the signers" % source)
        else:
            text = read_text(source, "signers file" if self.args.signers else None)
            need(text is not None, "cannot read %s" % source)
        self.roles = parse_signers(text)
        need(self.roles, "%s has no line with a coco-role= comment" % source)
        self.signers_file = write_file(os.path.join(self.tmp, "allowed_signers"),
                                       text.encode("utf-8"))

    def eval_signoff(self, entry, stage, want_artifact, expected_prev, want_sha=None):
        for key in ("signer", "artifact", "sha256", "at", "repo", "branch", "stage",
                    "base", "size"):
            if not isinstance(entry.get(key), str) or not entry.get(key):
                return False, "sign-off is missing %s" % key
        for key, want in (("repo", self.repo), ("branch", self.branch),
                          ("stage", stage), ("size", self.gate["size"])):
            if entry[key] != want:
                return False, "signed for %s %s, not %s" % (key, entry[key], want)
        if not re.match(r"^[0-9a-f]{40}$", entry["base"]):
            return False, "base is not a 40-hex commit: %s" % entry["base"]
        refs = ("HEAD", "origin/" + self.base) if self.ci else ("HEAD",)
        if not all(is_ancestor(entry["base"], ref) for ref in refs):
            return False, "sign-off not on this history"
        if want_artifact is not None and entry["artifact"] != want_artifact:
            return False, "signed artifact %s is not %s" % (entry["artifact"],
                                                            want_artifact)
        if stage not in ("size", "infra") and not safe_rel(entry["artifact"]):
            return False, "artifact path escapes the repo: %s" % entry["artifact"]
        found = self.roles.get(entry["signer"])
        if found is None:
            return False, "signer %s is not in %s" % (entry["signer"], SIGNERS_PATH)
        role = found[0]
        if role in self.policy["no_sign_roles"]:
            return False, "role %s may never sign (no_sign_roles)" % role
        allowed = self.policy["stages"].get(POLICY_STAGE.get(stage, stage), [])
        if role not in allowed:
            return False, "role %s may not sign %s (allowed: %s)" % (
                role, stage, ", ".join(allowed) or "none")
        if entry["signer"] == self.gate["builder"]:
            return False, "signer %s is the gate builder" % entry["signer"]
        if expected_prev is not None and entry.get("prev", "") != expected_prev:
            return False, "prev does not match the %s message" % prev_stage(stage)
        if not ssh_verify(self.signers_file, entry["signer"],
                          canonical(entry), entry["sig"]):
            return False, "signature does not verify"
        if stage in ("size", "infra"):
            if entry["sha256"] != (want_sha or sha_hex(b"small")):
                return False, "artifact changed after signing: %s" % entry["artifact"]
            return True, ""
        if not os.path.isfile(entry["artifact"]):
            return False, "artifact missing: %s" % entry["artifact"]
        if sha_file(entry["artifact"]) != entry["sha256"]:
            return False, "artifact changed after signing: %s" % entry["artifact"]
        return True, ""

    def pick(self, stage, want_artifact, expected_prev, label, want_sha=None):
        entries = sorted((e for e in self.gate.get("signoffs", [])
                          if isinstance(e, dict) and e.get("stage") == stage),
                         key=lambda e: str(e.get("at", "")), reverse=True)
        if not entries:
            self.fail("no %s sign-off (%s)" % (stage, label), stage)
            return None
        reason = None
        for entry in entries:
            ok, why = self.eval_signoff(entry, stage, want_artifact, expected_prev, want_sha)
            if ok:
                return entry
            reason = reason or why
        self.fail(reason or ("no valid %s sign-off" % stage), stage)
        return None

    def check_stages(self):
        feature = any(glob_match(self.branch, p)
                      for p in self.policy["feature_branches"])
        if self.gate["size"] == "small":
            if not feature:
                self.notes.append("size=small: nothing further to check")
                return
            self.pick("size", "size:small", None, "unsigned size=small")
            return
        prev = None
        for stage in CHAIN:
            entry = self.pick(stage, self.gate["artifacts"][stage], prev,
                              "%s stage" % stage)
            if entry is None:
                return
            prev = sha_hex(canonical(entry).encode("utf-8"))

    def changed_files(self):
        text = None
        if self.args.changed:
            text = read_text(self.args.changed, "changed-files list")
        elif self.ci:
            text = git_text(["diff", "--name-only", "%s...HEAD" % self.base_ref])
            need(text is not None,
                 "cannot list changed files against %s" % self.base_ref)
        return [line.strip() for line in (text or "").splitlines() if line.strip()]

    def numstat_total(self):
        if self.args.changed_numstat:
            text = read_text(self.args.changed_numstat, "numstat list")
        elif self.ci:
            text = git_text(["diff", "--numstat", "%s...HEAD" % self.base_ref])
            need(text is not None,
                 "cannot count changed lines against %s" % self.base_ref)
        else:
            return 0
        total = 0
        for raw in (text or "").splitlines():
            added, deleted, path = (raw.split("\t") + ["", "", ""])[:3]
            if not (added.isdigit() and deleted.isdigit()):
                continue
            # Only Markdown prose is free. Code under docs/ or tests/ counts like any
            # other code, or a feature could ride in under those folders ungated.
            if path.endswith(".md"):
                continue
            total += int(added) + int(deleted)
        return total

    def check_protected(self):
        paths = protected_hits("\n".join(self.changed_files()), self.policy)
        if not paths:
            return
        if git_text(["show", "%s:scripts/coco_gate.py" % self.base_ref]) is None:
            self.notes.append("protected path changed (%s); bootstrap PR, rule skipped"
                              % ", ".join(paths))
            return
        label = "protected path changed without infra sign-off: %s" % ", ".join(paths)
        if self.gate is None:
            self.fail(label)
            return
        digest = infra_hex(paths)
        if self.pick("infra", "infra:" + digest, None, label, digest) is None:
            self.fail(label)

    def check_ui(self):
        hits = [p for p in self.changed_files()
                if any(glob_match(p, g) for g in self.gate.get("ui", []))]
        if not hits:
            return
        mock = self.pick("mock", None, None,
                         "ui files changed: %s" % ", ".join(hits[:3]))
        if mock is None:
            return
        approve = self.pick("approve", mock["artifact"], None,
                            "the mock needs an approval")
        if approve is None:
            return
        if self.policy["approver_key"] == "sk":
            role, keytype = self.roles.get(approve["signer"], ("", ""))
            if role != "approver":
                self.fail("signer role %s is not approver (approver_key=sk)" % role,
                          "approve")
            elif not keytype.startswith("sk-"):
                self.fail("approver key is not an sk- key (%s)" % keytype, "approve")
            return
        decision = approve.get("decision", "")
        if not isinstance(decision, str) or not decision.strip():
            self.fail("approve sign-off has no decision record", "approve")
            return
        text = None if not safe_rel(decision) else \
            (git_text(["show", "%s:%s" % (self.base_ref, decision)])
             if self.ci else read_text(decision))
        if text is None:
            self.fail("decision record %s is not on %s"
                      % (decision, self.base_ref if self.ci else "the base tree"),
                      "approve")
        elif not re.search(r"(?m)^\s*by:\s*\S+", text):
            self.fail("decision record %s has no 'by: <id>' line" % decision, "approve")
        elif approve["artifact"] not in text:
            # Bind the relayed yes to this mock: any record with a by: line won't do.
            self.fail("decision record %s does not name the mock %s"
                      % (decision, approve["artifact"]), "approve")

    def absent_gate(self):
        # Base first: otherwise the feature rule fires and the deletion is never named.
        if git_text(["show", "%s:%s" % (self.base_ref, self.path)]) is not None:
            self.fail("gate %s exists on %s but was deleted on this branch"
                      % (self.path, self.base_ref))
        elif any(glob_match(self.branch, p) for p in self.policy["feature_branches"]):
            self.fail("no gate for feature branch %s (expected %s)"
                      % (self.branch, self.path))
        else:
            lines, limit = self.numstat_total(), self.policy["small_max_lines"]
            if lines > limit:
                self.fail("no gate and %d changed lines (limit %d)" % (lines, limit))
            else:
                self.notes.append("no gate: not a feature branch, %d changed lines"
                                  % lines)
        self.check_protected()
        return self.finish()

    def run(self):
        self.tmp = tempfile.mkdtemp(prefix="coco-gate-")
        try:
            check_ssh()
            # A repo adopts the workflow by putting .coco/allowed_signers on its base
            # branch. Until then there is nobody who could sign, so the check reports
            # and passes. Adding the file is itself a protected-path change.
            # Fail closed: only a readable base tree that lacks the file counts as
            # not adopted. An unreadable or unfetched base is a FAIL, never a pass.
            if self.ci and not self.args.signers:
                code, out, _err = git(["ls-tree", "--name-only", self.base_ref, "--", SIGNERS_PATH])
                need(code == 0, "cannot read the base tree %s; fetch it first" % self.base_ref)
                if not out.strip():
                    say("ok not adopted: no %s on %s" % (SIGNERS_PATH, self.base_ref))
                    return 0
            self.policy = self.load_policy()
            text = read_text(self.path)
            if text is None:
                return self.absent_gate()
            self.gate = check_gate(parse_json(text, self.path), self.path)
            for key, want in (("branch", self.branch), ("repo", self.repo)):
                if self.gate[key] != want:
                    self.fail("gate is for %s %s, not %s"
                              % (key, self.gate[key], want))
            self.load_signers()
            self.check_stages()
            self.check_ui()
            self.check_protected()
            return self.finish()
        finally:
            shutil.rmtree(self.tmp, ignore_errors=True)


def cmd_init(args):
    path = gate_path(args.branch)
    need(not os.path.exists(path) or args.force,
         "%s already exists; pass --force to overwrite" % path)
    artifacts = {s: getattr(args, s) for s in CHAIN if getattr(args, s)}
    need(args.size == "small" or len(artifacts) == len(CHAIN),
         "a feature gate needs --prd, --arch and --plan")
    for name in artifacts.values():
        need(safe_rel(name), "not a repo-relative path: %s" % one_line(name))
    gate = {"schema": 1, "repo": repo_slug(), "branch": args.branch,
            "size": args.size, "builder": args.builder, "ui": list(args.ui or []),
            "signoffs": [], "artifacts": artifacts}
    write_json(path, gate)
    say("wrote %s (%s)" % (path, args.size))
    return 0


def cmd_sign(args):
    branch = args.branch or os.environ.get("GITHUB_HEAD_REF", "") or current_branch()
    path = gate_path(branch)
    gate = check_gate(parse_json(read_text(path, "gate file"), path), path)
    base = args.base_commit or merge_base(args.base or "main")
    artifact, digest = "size:small", sha_hex(b"small")
    if args.stage == "infra":
        # The base commit's policy, not the work tree's: verify must hash the same set.
        policy = load_policy(git_text(["show", "%s:%s" % (base, POLICY_PATH)]),
                             "%s:%s" % (base, POLICY_PATH))
        paths = protected_hits(git_text(["diff", "--name-only", "%s...HEAD" % base])
                               or "", policy)
        need(paths, "no protected path changed against %s" % base)
        digest = infra_hex(paths)
        artifact = "infra:" + digest
    elif args.stage != "size":
        artifact = args.artifact or (gate.get("artifacts") or {}).get(args.stage, "")
        need(artifact, "%s needs --artifact" % args.stage)
        need(safe_rel(artifact), "not a repo-relative path: %s" % artifact)
        need(os.path.isfile(artifact), "artifact missing: %s" % artifact)
        digest = sha_file(artifact)
    entry = {"repo": gate["repo"], "branch": branch, "base": base,
             "stage": args.stage, "size": gate["size"], "artifact": artifact,
             "sha256": digest, "prev": "", "decision": args.decision or "",
             "signer": args.signer,
             "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if args.stage in ("arch", "plan"):
        parent = latest(gate, prev_stage(args.stage))
        need(parent is not None, "cannot sign %s: no %s sign-off to chain from"
             % (args.stage, prev_stage(args.stage)))
        entry["prev"] = sha_hex(canonical(parent).encode("utf-8"))
    entry["sig"] = ssh_sign(args.key, canonical(entry))
    gate.setdefault("signoffs", []).append(entry)
    write_json(path, gate)
    say("signed %s as %s (%s)" % (args.stage, args.signer, artifact))
    return 0


def cmd_status(args):
    branch = args.branch or os.environ.get("GITHUB_HEAD_REF", "") or current_branch()
    path = gate_path(branch)
    text = read_text(path)
    if text is None:
        print("stage none; next: init (%s)" % path)
        return 0
    gate = check_gate(parse_json(text, path), path)
    last = ([s for s in CHAIN if latest(gate, s) is not None] or [None])[-1]
    if last is None:
        print("stage none; next: %s" % (gate.get("artifacts") or {}).get("prd", "sign"))
    elif last == CHAIN[-1]:
        print("stage %s; next: build" % last)
    else:
        nxt = CHAIN[CHAIN.index(last) + 1]
        print("stage %s; next: %s" % (last, (gate.get("artifacts") or {}).get(nxt) or "sign " + nxt))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="coco_gate.py", description="The coco-workflow gate.")
    subs = parser.add_subparsers(dest="cmd")
    init = subs.add_parser("init", help="write the gate file for a branch")
    init.add_argument("--size", required=True, choices=("feature", "small"))
    init.add_argument("--ui", nargs="*", default=[])
    init.add_argument("--force", action="store_true")
    for flag in ("--branch", "--builder", "--prd", "--arch", "--plan"):
        init.add_argument(flag, required=flag in ("--branch", "--builder"))
    sign = subs.add_parser("sign", help="sign a stage with a named key")
    sign.add_argument("--stage", required=True, choices=STAGES)
    for flag in ("--signer", "--key"):
        sign.add_argument(flag, required=True)
    for flag in ("--artifact", "--decision", "--branch", "--base", "--base-commit"):
        sign.add_argument(flag)
    verify = subs.add_parser("verify", help="check the gate for a branch")
    verify.add_argument("--ci", action="store_true")
    for flag in ("--base", "--signers", "--policy", "--branch", "--changed",
                 "--changed-numstat"):
        verify.add_argument(flag)
    status = subs.add_parser("status", help="print the stage and the next artifact")
    status.add_argument("--branch")
    return parser


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 2
    try:
        return {"init": cmd_init, "sign": cmd_sign, "status": cmd_status,
                "verify": lambda a: Check(a).run()}[args.cmd](args)
    except GateError as exc:
        say("FAIL " + one_line(exc))
        return 1
    except Exception as exc:  # fail closed: never a traceback
        say("FAIL unexpected error: %s" % one_line(repr(exc)))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
