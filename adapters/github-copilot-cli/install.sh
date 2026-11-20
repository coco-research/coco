#!/usr/bin/env bash
# GitHub Copilot CLI adapter — wires Coco MCP server, skills, custom agents,
# and project instructions for GitHub Copilot CLI.
#
# Where things land:
#   Coco MCP server                  -> ~/.copilot/mcp-config.json                (merged)
#   skills/<name>/                   -> ~/.copilot/skills/<name>                  (symlink)
#   systems/<bundle>/skills/<name>/  -> ~/.copilot/skills/<name>                  (symlink)
#   systems/<bundle>/<team>/         -> ~/.copilot/skills/<frontmatter name>      (symlink)
#   agents/<name>.md                 -> ~/.copilot/agents/<name>.agent.md         (symlink)
#   systems/<bundle>/agents/*.md     -> ~/.copilot/agents/<name>.agent.md         (symlink)
#   project agent catalog            -> ./AGENTS.md                               (generated)
#   project Copilot instructions     -> ./.github/copilot-instructions.md         (generated)
#
# Usage:
#   bash adapters/github-copilot-cli/install.sh                    # core + default bundles
#   bash adapters/github-copilot-cli/install.sh --core-only        # core only, no bundles
#   bash adapters/github-copilot-cli/install.sh --systems gsd      # only these bundles
#   bash adapters/github-copilot-cli/install.sh --dry-run          # preview only
#   bash adapters/github-copilot-cli/install.sh --uninstall        # remove Coco entries & links

set -euo pipefail
unset CDPATH

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ -n "${COPILOT_HOME+x}" && -z "$COPILOT_HOME" ]] && { echo "Refusing to run: COPILOT_HOME must not be empty or /." >&2; exit 1; }
COPILOT_HOME="${COPILOT_HOME:-$HOME/.copilot}"
[[ -z "$COPILOT_HOME" || "$COPILOT_HOME" == "/" || "$COPILOT_HOME" == "//" ]] && { echo "Refusing to run: COPILOT_HOME must not be empty or /." >&2; exit 1; }

DRY_RUN=0
CORE_ONLY=0
UNINSTALL=0
EXPLICIT_SYSTEMS=0
SYSTEMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --core-only) CORE_ONLY=1 ;;
    --systems)
      shift
      [[ $# -gt 0 ]] || { echo "--systems requires a value" >&2; exit 1; }
      EXPLICIT_SYSTEMS=1
      IFS=',' read -ra SYSTEMS <<< "$1"
      ;;
    --uninstall) UNINSTALL=1 ;;
    --help|-h) bash "$REPO_ROOT/scripts/print-usage.sh" "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

command -v python3 >/dev/null 2>&1 || { echo "python3 is required by github-copilot-cli adapter." >&2; exit 1; }

if [[ $UNINSTALL -eq 0 ]]; then
  if [[ $CORE_ONLY -eq 1 ]]; then
    SYSTEMS=()
  elif [[ $EXPLICIT_SYSTEMS -eq 0 ]]; then
    while IFS= read -r b; do [[ -n "$b" ]] && SYSTEMS+=("$b"); done \
      < <(bash "$REPO_ROOT/scripts/installable-bundles.sh" --one-per-line 2>/dev/null || true)
  fi
fi

SYSTEMS_CSV=""
[[ ${#SYSTEMS[@]} -gt 0 ]] && SYSTEMS_CSV="$(IFS=,; printf '%s' "${SYSTEMS[*]}")"

python3 - "$UNINSTALL" "$DRY_RUN" "$REPO_ROOT" "$COPILOT_HOME" "$SYSTEMS_CSV" <<'PY'
import contextlib, hashlib, importlib.util, json, os, pathlib, re, shutil, sys, tempfile, time

uninstall_s, dry_s, repo_s, home_s, systems_csv = sys.argv[1:6]
uninstall, dry = uninstall_s == "1", dry_s == "1"
repo_root, copilot_home = pathlib.Path(repo_s), pathlib.Path(home_s)
repo_phys, cwd_phys = repo_root.resolve(), pathlib.Path.cwd().resolve()
in_checkout = cwd_phys == repo_phys or repo_phys in cwd_phys.parents
systems = [s.strip() for s in systems_csv.split(",") if s.strip()]

cfg_path = copilot_home / "mcp-config.json"
bak_path = copilot_home / "mcp-config.json.bak"
marker_path = pathlib.Path(str(cfg_path) + ".coco-mcp")
legacy_marker = copilot_home / ".coco-mcp"
SKIP_AGENTS = {"INDEX", "README", "PROMPT-DEFENSE"}
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
COCO_SERVER = {"type": "local", "command": "npx", "args": ["-y", "cocosuperintelligence", "mcp"], "tools": ["*"]}

def rmdir_quiet(p):
    if not dry and p.is_dir() and not p.is_symlink():
        with contextlib.suppress(OSError):
            p.rmdir()

def is_coco_link(p):
    if not p.is_symlink():
        return False
    raw = os.readlink(p)
    if any(raw.startswith(str(r) + os.sep) for r in (repo_root, repo_phys)):
        return True
    return p.exists() and str(p.resolve()).startswith(str(repo_phys) + os.sep)

def frontmatter_name(skill_md):
    lines = skill_md.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].rstrip("\r") != "---":
        return ""
    for line in (ln.rstrip("\r") for ln in lines[1:]):
        if line == "---":
            break
        if line.startswith("name:"):
            val = line[5:].strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                val = val[1:-1]
            return val if SLUG_RE.match(val) and ".." not in val else ""
    return ""

def write_atomic(target, payload, perm=None):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".coco-tmp.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(payload)
        if perm is not None:
            os.chmod(tmp_name, perm)
        os.replace(tmp_name, target)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise

def is_untouched_coco(path):
    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError:
        return False
    if not lines or "coco-generated sha256=" not in lines[0]:
        return False
    tag = lines[0].split("coco-generated sha256=", 1)[1][:64]
    return len(tag) == 64 and all(c in "0123456789abcdef" for c in tag) and (
        hashlib.sha256("".join(lines[1:]).encode("utf-8")).hexdigest() == tag
    )

if cfg_path.is_symlink() or (cfg_path.exists() and not cfg_path.is_file()):
    sys.exit(f"Refusing to modify non-regular MCP config: {cfg_path}")

if uninstall:
    for sub in ("skills", "agents"):
        d = copilot_home / sub
        if not d.is_symlink() and d.is_dir():
            for entry in sorted(d.iterdir()):
                if is_coco_link(entry):
                    print(f"DRY: rm -- {entry}" if dry else f"Removed link: {entry}")
                    if not dry:
                        entry.unlink()
            rmdir_quiet(d)
    cfg_unreadable = False
    if cfg_path.is_file():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            sys.stderr.write(f"Warning: skipping unreadable MCP config {cfg_path} ({exc.__class__.__name__}); inspect manually.\n")
            data = None
            cfg_unreadable = True
        if isinstance(data, dict) and isinstance(data.get("mcpServers"), dict) and "coco" in data["mcpServers"]:
            if dry:
                print(f"DRY: remove mcpServers.coco from {cfg_path}")
            else:
                perm = cfg_path.stat().st_mode & 0o777
                del data["mcpServers"]["coco"]
                write_atomic(cfg_path, (json.dumps(data, indent=2) + "\n").encode("utf-8"), perm)
                print(f"Removed mcpServers.coco from {cfg_path}")
    if not cfg_unreadable:
        for mp in (marker_path, legacy_marker):
            if mp.exists() or mp.is_symlink():
                if dry: print(f"DRY: rm {mp}")
                else: mp.unlink()
    if not in_checkout:
        for rel in ("AGENTS.md", ".github/copilot-instructions.md"):
            p = pathlib.Path(rel)
            if not p.is_symlink() and p.is_file() and is_untouched_coco(p):
                if dry: print(f"DRY: rm {rel}")
                else: p.unlink(); print(f"Removed: {rel}")
        rmdir_quiet(pathlib.Path(".github"))
    rmdir_quiet(copilot_home)
    print("Done.")
    sys.exit(0)

for s in systems:
    if not (repo_root / "systems" / s).is_dir():
        sys.stderr.write(f"Unknown system: {s}\n")
        sys.exit(1)

print("Coco · GitHub Copilot CLI adapter")
print(f"Source: {repo_root}\nTarget: {copilot_home} (MCP, skills, agents) + {pathlib.Path.cwd()} (project instructions)")
print(f"Bundles: {','.join(systems) if systems else 'core only'}")
if dry:
    print("(dry-run mode)")

def link_entry(src, dst):
    src_s = str(src).rstrip(os.sep)
    if dst.exists() and not dst.is_symlink():
        print(f"Skip (existing user path): {dst}"); return 0
    if dst.is_symlink() and not is_coco_link(dst):
        print(f"Skip (foreign symlink): {dst} -> {os.readlink(dst)}"); return 0
    if dry:
        print(f"DRY: ln -s {src_s} {dst}"); return 1
    if dst.is_symlink():
        if os.readlink(dst) == src_s: return 1
        dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(src_s, dst)
    return 1

def link_skills_dir(base):
    return sum(link_entry(d, copilot_home / "skills" / d.name) for d in sorted(base.glob("*")) if (d / "SKILL.md").is_file()) if base.is_dir() else 0

def link_agents_dir(base):
    return sum(link_entry(a, copilot_home / "agents" / f"{a.stem}.agent.md") for a in sorted(base.glob("*.md")) if a.stem not in SKIP_AGENTS) if base.is_dir() else 0

existed = cfg_path.is_file()
perm = (cfg_path.stat().st_mode & 0o777) if existed else 0o600
if existed:
    try:
        raw = cfg_path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        sys.exit(f"Refusing to modify unreadable or malformed MCP config {cfg_path}: {exc}")
    if not isinstance(data, dict) or not isinstance(data.setdefault("mcpServers", {}), dict):
        sys.exit(f"Invalid mcpServers structure in {cfg_path}")
else:
    raw, data = b"", {"mcpServers": {}}

n_skills = link_skills_dir(repo_root / "skills")
n_agents = link_agents_dir(repo_root / "agents")
for s in systems:
    sroot = repo_root / "systems" / s
    n_skills += link_skills_dir(sroot / "skills")
    for tdir in sorted(p for p in sroot.iterdir() if p.is_dir() and p.name != "skills" and (p / "SKILL.md").is_file()):
        n_skills += link_entry(tdir, copilot_home / "skills" / (frontmatter_name(tdir / "SKILL.md") or tdir.name))
    n_agents += link_agents_dir(sroot / "agents")
data["mcpServers"]["coco"] = COCO_SERVER
out = (json.dumps(data, indent=2) + "\n").encode("utf-8")
has_marker = marker_path.exists() or legacy_marker.exists()
if existed and raw == out:
    if not dry and not marker_path.exists():
        marker_path.write_text("# managed-by: coco\n", encoding="utf-8")
    print(f"{'DRY: unchanged' if dry else 'Unchanged:'} {cfg_path}")
else:
    need_bak = existed and not has_marker
    if dry:
        if need_bak: print(f"DRY: backup {cfg_path} -> {bak_path}")
        print(f"DRY: write {cfg_path}")
    else:
        copilot_home.mkdir(parents=True, exist_ok=True)
        if need_bak:
            shutil.copy2(cfg_path, bak_path)
            print(f"Backed up existing {cfg_path} -> {bak_path}")
        write_atomic(cfg_path, out, perm)
        marker_path.write_text("# managed-by: coco\n", encoding="utf-8")
        print(f"Wrote: {cfg_path}")

if not in_checkout:
    spec = importlib.util.spec_from_file_location("fm_desc", repo_root / "scripts" / "frontmatter-description.py")
    fm_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fm_mod)
    def agent_block(heading, adir):
        rows = [heading, ""]
        for ag in sorted(adir.glob("*.md")):
            if ag.stem not in SKIP_AGENTS:
                rows += [f"### {ag.stem}", fm_mod.description(ag)[:160], ""]
        return rows
    blines = agent_block("## Available Agents", repo_root / "agents")
    for s in systems:
        adir = repo_root / "systems" / s / "agents"
        if adir.is_dir():
            blines += agent_block(f"## System: {s} Agents", adir)
    agents_body = "\n".join(blines) + "\n"
    instr_body = (
        "\n## Code Conventions\n- Follow existing project patterns and naming conventions\n"
        "- Use conventional commits for all commit messages\n- Always run tests before committing changes\n"
        "- Prefer explicit imports over wildcard imports\n\n## Security\n"
        "- Never hardcode secrets, API keys, or credentials\n- Validate all user input before processing\n"
        "- Use parameterized queries for database operations\n- Sanitize output to prevent injection attacks\n\n"
        "## Testing\n- Write tests for new functionality\n- Ensure existing tests pass before submitting changes\n"
        "- Include edge cases and error handling in tests\n\n## Documentation\n"
        "- Update documentation when changing public APIs\n- Add inline comments for complex logic\n"
        "- Keep README and docs in sync with code changes\n"
    )
    for rel, hdr, body in (
        ("AGENTS.md", "# AGENTS.md — Generated by Coco for GitHub Copilot CLI", agents_body),
        (".github/copilot-instructions.md", "# Copilot Instructions — Generated by Coco", instr_body),
    ):
        t = pathlib.Path(rel)
        if t.is_symlink():
            print(f"{'DRY: skip' if dry else 'Skip'} (symlink preserved): {rel} -> {os.readlink(t)}")
            continue
        if t.exists() and not t.is_file():
            print(f"{'DRY: skip' if dry else 'Skip'} (non-regular path): {rel}")
            continue
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        full = f"{hdr} <!-- coco-generated sha256={digest} -->\n{body}".encode("utf-8")
        if dry:
            print(f"DRY: write {rel} ({len(full.splitlines())} lines)"); continue
        if t.is_file() and t.read_bytes() == full:
            print(f"Unchanged: {rel}"); continue
        if t.is_file() and not is_untouched_coco(t):
            bak = pathlib.Path(f"{rel}.bak")
            if bak.exists(): bak = pathlib.Path(f"{rel}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
            shutil.copy2(t, bak); print(f"Backed up existing {rel} -> {bak}")
        write_atomic(t, full, (t.stat().st_mode & 0o777) if t.is_file() else 0o644)
        print(f"Wrote: {rel}")

if not dry:
    print(f"Skills: {n_skills} linked into {copilot_home / 'skills'}\nAgents: {n_agents} linked into {copilot_home / 'agents'}")
print("Done.")
PY
