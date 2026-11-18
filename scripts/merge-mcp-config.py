#!/usr/bin/env python3
"""Idempotently merge Coco's stdio MCP server entry into an adapter config file.

Invariants:
- Reads JSON (with optional // and /* */ JSONC comments) or Continue YAML.
- Never overwrites a user-authored `coco` server entry; preserves all sibling entries.
- Writes `<config>.bak` before modifying any pre-existing file.
- Produces byte-identical files across re-runs (zero writes when unchanged).
"""
# ponytail: ceiling = JSON/JSONC + Continue YAML single-entry merger; upgrade path = full AST round-tripper if inline comment preservation is needed.

import argparse
import json
import os
import pathlib
import shutil
import sys
import tempfile


def strip_jsonc_comments(text):
    out = []
    i, n = 0, len(text)
    in_str = False
    esc = False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def is_coco_entry(entry):
    if not isinstance(entry, dict):
        return False
    tokens = []
    cmd = entry.get("command")
    if isinstance(cmd, str):
        tokens.append(cmd)
    elif isinstance(cmd, list):
        tokens.extend(str(x) for x in cmd)
    args = entry.get("args")
    if isinstance(args, list):
        tokens.extend(str(x) for x in args)
    for tok in tokens:
        norm = tok.replace("\\", "/")
        if "cocosuperintelligence" in norm or norm.endswith("/bin/coco.js") or norm == "bin/coco.js":
            return True
    return False


def write_atomic(target, data_bytes, mode=None):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data_bytes)
        if mode is not None:
            os.chmod(tmp_name, mode)
        os.replace(tmp_name, str(target))
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def merge_json(config_path, repo_real, root_key, dry_run):
    cli_path = os.path.realpath(os.path.join(repo_real, "bin", "coco.js"))
    marker_path = pathlib.Path(str(config_path) + ".coco-mcp")
    marker_bytes = f"# managed-by: coco\nrepo: {repo_real}\n".encode("utf-8")

    existed = config_path.exists()
    orig_bytes = b""
    orig_mode = None
    doc = {}

    if existed:
        st = config_path.stat()
        orig_mode = st.st_mode & 0o777
        orig_bytes = config_path.read_bytes()
        raw_text = orig_bytes.decode("utf-8")
        cleaned = strip_jsonc_comments(raw_text).strip()
        if cleaned:
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError as exc:
                sys.stderr.write(f"Skip MCP: cannot parse JSON in {config_path} ({exc})\n")
                return 0
            if not isinstance(parsed, dict):
                sys.stderr.write(f"Skip MCP: top-level JSON in {config_path} is not an object\n")
                return 0
            doc = parsed

    servers = doc.get(root_key)
    if servers is None:
        servers = {}
        doc[root_key] = servers
    elif not isinstance(servers, dict):
        sys.stderr.write(f"Skip MCP: '{root_key}' in {config_path} is not an object\n")
        return 0

    if "coco" in servers:
        coco_owned = marker_path.is_file() or is_coco_entry(servers["coco"])
        if not coco_owned:
            print(f"Skip MCP: user 'coco' entry kept in {config_path}")
            return 0

    servers["coco"] = {
        "command": "node",
        "args": [cli_path, "mcp"],
    }
    rendered_bytes = (json.dumps(doc, indent=2) + "\n").encode("utf-8")

    if existed and orig_bytes == rendered_bytes and marker_path.is_file() and marker_path.read_bytes() == marker_bytes:
        print(f"MCP unchanged: {config_path}")
        return 0

    if dry_run:
        print(f"DRY: merge coco MCP entry ({root_key}) into {config_path}")
        return 0

    if existed and orig_bytes != rendered_bytes:
        bak_path = pathlib.Path(str(config_path) + ".bak")
        shutil.copy2(str(config_path), str(bak_path))
        print(f"Backed up {config_path} -> {bak_path}")

    if not existed or orig_bytes != rendered_bytes:
        write_atomic(config_path, rendered_bytes, mode=orig_mode)
    if not marker_path.is_file() or marker_path.read_bytes() != marker_bytes:
        write_atomic(marker_path, marker_bytes)

    print(f"Configured MCP: {config_path} ({root_key}.coco)")
    return 0


def merge_continue_yaml(config_path, repo_real, dry_run):
    cli_path = os.path.realpath(os.path.join(repo_real, "bin", "coco.js"))
    rendered = "\n".join([
        "# managed-by: coco",
        "name: coco",
        "version: 1.0.0",
        "schema: v1",
        "mcpServers:",
        "  - name: coco",
        '    command: "node"',
        f"    args: [{json.dumps(cli_path)}, \"mcp\"]",
        "",
    ])
    rendered_bytes = rendered.encode("utf-8")

    existed = config_path.exists()
    orig_bytes = b""
    orig_mode = None
    if existed:
        orig_mode = config_path.stat().st_mode & 0o777
        orig_bytes = config_path.read_bytes()
        text = orig_bytes.decode("utf-8", errors="replace")
        first_line = text.splitlines()[0].strip() if text.splitlines() else ""
        if first_line != "# managed-by: coco":
            print(f"Skip MCP: user entry kept in {config_path}")
            return 0
        if orig_bytes == rendered_bytes:
            print(f"MCP unchanged: {config_path}")
            return 0

    if dry_run:
        print(f"DRY: write coco Continue MCP config to {config_path}")
        return 0

    if existed:
        bak_path = pathlib.Path(str(config_path) + ".bak")
        shutil.copy2(str(config_path), str(bak_path))
        print(f"Backed up {config_path} -> {bak_path}")

    write_atomic(config_path, rendered_bytes, mode=orig_mode)
    print(f"Configured MCP: {config_path}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Merge Coco MCP server entry into an adapter config.")
    ap.add_argument("--format", choices=("json", "continue-yaml"), required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--key", default="mcpServers")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    config_path = pathlib.Path(args.config)
    repo_real = os.path.realpath(args.repo_root)
    if args.format == "continue-yaml":
        return merge_continue_yaml(config_path, repo_real, args.dry_run)
    return merge_json(config_path, repo_real, args.key, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
