#!/usr/bin/env python3
"""Summarize SkillSpector JSON reports by schema; fail closed on severe or malformed output.

Shared by the scan and fixture jobs in .github/workflows/skill-scan.yml.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import pathlib
import re
import sys

ALLOWED_SEVERITIES = {"info", "low", "medium", "high", "critical"}
SEVERE = {"high", "critical"}
ALLOWED_BRIDGE_ENV = {
    "M0_BASE_URL",
    "M0_HTTP_TIMEOUT",
    "M0_PROJECT",
    "M0_SOURCE_TOOL",
    "M0_MCP_TRANSPORT",
}
DENY_ENV_RE = re.compile(r"KEY|TOKEN|SECRET|PASS|AUTH|CRED", re.IGNORECASE)
FORBIDDEN_NET_MODS = {
    "http", "http.client", "socket", "ssl", "requests", "httpx", "urllib3",
    "aiohttp", "ftplib", "smtplib", "telnetlib", "xmlrpc", "websocket",
    "websockets", "subprocess",
}
ENV_ATTRS = {"environ", "environb", "getenv", "getenvb", "putenv"}
BRIDGE_FORBIDDEN_CALLS = {"getattr", "__import__", "vars", "globals", "exec", "eval"}
SIBLING_FORBIDDEN_CALLS = {"__import__", "exec", "eval"}


def _is_num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_line(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 1


def _text(v: object) -> str:
    return v.strip() if isinstance(v, str) else ""


def _cmd(text: str) -> str:
    escaped = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return "".join("?" if (ord(c) < 32 or ord(c) == 127) else c for c in escaped)


def _norm_dir(d: str) -> str:
    return os.path.normpath(d.strip())


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _str_const(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _check_bridge_file(path: pathlib.Path) -> list[str]:
    errs: list[str] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return [f"bridge check: cannot parse {path.name} ({exc})"]

    parents = _parent_map(tree)
    allowed_env_attrs: set[ast.AST] = set()
    transport_calls: list[ast.Call] = []
    urlopen_calls = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod, root = alias.name, alias.name.split(".")[0]
                if mod in FORBIDDEN_NET_MODS or root in FORBIDDEN_NET_MODS or root in {"importlib", "posix", "nt"}:
                    errs.append(f"bridge check: forbidden import {mod}")
                elif mod in {"os", "urllib", "urllib.request"} and alias.asname:
                    errs.append(f"bridge check: aliased import {mod}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = mod.split(".")[0]
            if root in {"os", "posix", "nt", "importlib"} or mod in FORBIDDEN_NET_MODS or root in FORBIDDEN_NET_MODS:
                errs.append(f"bridge check: forbidden from-import {mod}")
            elif mod == "urllib" and any(a.name == "request" for a in node.names):
                errs.append("bridge check: forbidden from urllib import request")
            elif mod == "urllib.request":
                errs.append("bridge check: forbidden from urllib.request import")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BRIDGE_FORBIDDEN_CALLS:
                errs.append(f"bridge check: forbidden call {node.func.id}")
            elif isinstance(node.func, ast.Attribute) and (
                node.func.attr in BRIDGE_FORBIDDEN_CALLS
                or node.func.attr in {"import_module", "system", "popen"}
            ):
                errs.append(f"bridge check: forbidden call .{node.func.attr}")

            env_attr: ast.AST | None = None
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "environ"
                and isinstance(node.func.value.value, ast.Name)
                and node.func.value.value.id == "os"
            ):
                env_attr = node.func.value
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "getenv"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"
            ):
                env_attr = node.func

            if env_attr is not None:
                key = _str_const(node.args[0]) if node.args and not node.keywords else None
                if key is None:
                    errs.append("bridge check: non-literal env key")
                else:
                    if DENY_ENV_RE.search(key):
                        errs.append(f"bridge check: credential-named env key {key}")
                    elif key not in ALLOWED_BRIDGE_ENV:
                        errs.append(f"bridge check: disallowed env key {key}")
                    else:
                        allowed_env_attrs.add(env_attr)
                        if key == "M0_MCP_TRANSPORT":
                            transport_calls.append(node)

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ENV_ATTRS and node not in allowed_env_attrs:
            errs.append(f"bridge check: disallowed env reference .{node.attr}")
        elif isinstance(node, ast.Name) and node.id in ENV_ATTRS:
            errs.append(f"bridge check: disallowed env name {node.id}")
        elif (
            isinstance(node, ast.Attribute)
            and node.attr == "request"
            and isinstance(node.value, ast.Name)
            and node.value.id == "urllib"
        ):
            p = parents.get(node)
            if not (
                isinstance(p, ast.Attribute)
                and p.value is node
                and p.attr in {"Request", "urlopen"}
                and isinstance(parents.get(p), ast.Call)
                and parents[p].func is p
            ):
                errs.append("bridge check: disallowed urllib.request usage")
            elif p.attr == "urlopen":
                urlopen_calls += 1

    if urlopen_calls != 1:
        errs.append(f"bridge check: expected exactly 1 urllib.request.urlopen call, found {urlopen_calls}")

    if len(transport_calls) != 1:
        errs.append(f"bridge check: expected exactly 1 M0_MCP_TRANSPORT read, found {len(transport_calls)}")
    else:
        cur: ast.AST = transport_calls[0]
        while True:
            p = parents.get(cur)
            if isinstance(p, ast.Attribute) and p.value is cur and p.attr in {"strip", "lower"}:
                gp = parents.get(p)
                if isinstance(gp, ast.Call) and gp.func is p and not gp.args and not gp.keywords:
                    cur = gp
                    continue
            break
        assign = parents.get(cur)
        if not (
            isinstance(assign, ast.Assign)
            and assign in tree.body
            and assign.value is cur
            and len(assign.targets) == 1
            and isinstance(assign.targets[0], ast.Name)
        ):
            errs.append("bridge check: M0_MCP_TRANSPORT must assign to one module-level name")
        else:
            tname = assign.targets[0].id
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == tname:
                    if node is assign.targets[0]:
                        continue
                    p = parents.get(node)
                    if not (
                        isinstance(node.ctx, ast.Load)
                        and isinstance(p, ast.Compare)
                        and (p.left is node or node in p.comparators)
                    ):
                        errs.append(f"bridge check: {tname} may only be used in a Compare")
    return errs


def _check_sibling_file(path: pathlib.Path, scripts_dir: pathlib.Path) -> list[str]:
    errs: list[str] = []
    rel = path.relative_to(scripts_dir).as_posix()
    is_m0_server = path.parent == scripts_dir and path.name == "m0_server.py"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return [f"sibling check ({rel}): cannot parse ({exc})"]

    allowed_env: set[ast.AST] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod, root = alias.name, alias.name.split(".")[0]
                if mod == "http.server" and is_m0_server:
                    continue
                if (
                    mod in FORBIDDEN_NET_MODS
                    or root in FORBIDDEN_NET_MODS
                    or mod == "urllib.request"
                    or mod.startswith("urllib.request.")
                    or root in {"importlib", "posix", "nt"}
                ):
                    errs.append(f"sibling check ({rel}): forbidden import {mod}")
                elif mod in {"os", "urllib"} and alias.asname:
                    errs.append(f"sibling check ({rel}): aliased import {mod}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = mod.split(".")[0]
            if mod == "http.server" and is_m0_server:
                continue
            if (
                mod in FORBIDDEN_NET_MODS
                or root in FORBIDDEN_NET_MODS
                or mod == "urllib.request"
                or mod.startswith("urllib.request.")
                or (mod == "urllib" and any(a.name == "request" for a in node.names))
                or root in {"importlib", "posix", "nt"}
            ):
                errs.append(f"sibling check ({rel}): forbidden from-import {mod}")
            elif any(a.name in ENV_ATTRS and a.asname for a in node.names):
                errs.append(f"sibling check ({rel}): aliased env import")
        elif isinstance(node, ast.Attribute) and node.attr == "request" and isinstance(node.value, ast.Name) and node.value.id == "urllib":
            errs.append(f"sibling check ({rel}): forbidden urllib.request reference")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in (SIBLING_FORBIDDEN_CALLS | {"system", "popen"}):
                errs.append(f"sibling check ({rel}): forbidden call {node.func.id}")
            elif isinstance(node.func, ast.Attribute) and (
                node.func.attr in SIBLING_FORBIDDEN_CALLS
                or node.func.attr in {"system", "popen", "create_connection", "import_module"}
            ):
                errs.append(f"sibling check ({rel}): forbidden call .{node.func.attr}")
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "connect"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "socket"
            ):
                errs.append(f"sibling check ({rel}): forbidden call socket.connect")

            env_ref: ast.AST | None = None
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in {"get", "setdefault"}
                and (
                    (isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "environ"
                     and isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == "os")
                    or (isinstance(node.func.value, ast.Name) and node.func.value.id == "environ")
                )
            ):
                env_ref = node.func.value
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "getenv"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"
            ) or (isinstance(node.func, ast.Name) and node.func.id == "getenv"):
                env_ref = node.func

            if env_ref is not None:
                key = _str_const(node.args[0]) if node.args and not node.keywords else None
                if key is None:
                    errs.append(f"sibling check ({rel}): non-literal env key")
                else:
                    if DENY_ENV_RE.search(key):
                        errs.append(f"sibling check ({rel}): credential-named env key {key}")
                    allowed_env.add(env_ref)
        elif isinstance(node, ast.Subscript):
            env_ref = None
            if (
                isinstance(node.value, ast.Attribute)
                and node.value.attr == "environ"
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "os"
            ) or (isinstance(node.value, ast.Name) and node.value.id == "environ"):
                env_ref = node.value
            if env_ref is not None:
                key = _str_const(node.slice)
                if key is None:
                    errs.append(f"sibling check ({rel}): non-literal env subscript")
                else:
                    if DENY_ENV_RE.search(key):
                        errs.append(f"sibling check ({rel}): credential-named env key {key}")
                    allowed_env.add(env_ref)

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ENV_ATTRS and node not in allowed_env:
            errs.append(f"sibling check ({rel}): disallowed env reference .{node.attr}")
        elif isinstance(node, ast.Name) and node.id in ENV_ATTRS and node not in allowed_env:
            errs.append(f"sibling check ({rel}): disallowed env name {node.id}")
    return errs


# ponytail: 1 file, 1 rule, 4 request vars plus 1 transport selector. A PR can edit this file or summarize.py; kernel-owner review of any change under .github/skill-scan/** is the control. Upgrade path: per-sink taint tracking upstream, or a typed config module in the bridge.
# ponytail: values returned from sibling modules aren't traced into m0_mcp.py's Request; the shield is that no sibling can read a credential-named or unreadable env key, and none has an outbound path. Upgrade path: an inter-module taint pass, or a named allow-list per sibling (option a) if a sibling ever needs a secret.
def check_bridge(skill_dir: pathlib.Path) -> list[str]:
    scripts_dir = skill_dir / "scripts"
    bridge = scripts_dir / "m0_mcp.py"
    if not bridge.is_file():
        return [f"bridge check: {bridge} not found"]
    errs = _check_bridge_file(bridge)
    for py_file in sorted(scripts_dir.rglob("*.py")):
        if py_file == bridge:
            continue
        errs.extend(_check_sibling_file(py_file, scripts_dir))
    return errs


def summarize_dir(root: pathlib.Path, allow_suppressed: list[str] | None = None) -> int:
    problems: list[str] = []
    if not root.is_dir():
        print(f"::error::{_cmd(f'{root}: report directory not found')}")
        print(_cmd("0 report(s) checked, 1 problem(s)"))
        return 1

    allowed_map = {_norm_dir(d): pathlib.Path(d) for d in (allow_suppressed or [])}
    codes_path = root / "exit-codes.txt"
    lines = [ln for ln in codes_path.read_text(encoding="utf-8").splitlines() if ln.strip()] if codes_path.is_file() else []
    report_to_dir: dict[str, str] = {}
    for line in lines:
        parts = line.split("\t")
        code = parts[0].strip()
        where = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "<unknown>"
        rep_name = parts[2].strip() if len(parts) > 2 and parts[2].strip() else ""
        if rep_name:
            if rep_name in report_to_dir:
                problems.append(f"{rep_name}: duplicate mapping in exit-codes.txt")
            report_to_dir[rep_name] = where
        if code == "1":
            problems.append(f"{where}: skillspector exited 1, so the folder is above the default risk threshold")
        elif code != "0":
            problems.append(f"{where}: unexpected skillspector exit code {code!r}")

    reports = sorted(root.glob("*.json"))
    if not reports:
        problems.append("no report was written for any changed skill folder")
    elif len(reports) != len(lines):
        problems.append(f"{len(lines)} skill folder(s) scanned but {len(reports)} report(s) written")

    for report in reports:
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            problems.append(f"{report.name}: not a readable JSON report ({error})")
            continue
        if not isinstance(data, dict):
            problems.append(f"{report.name}: not a readable JSON report (expected object)")
            continue

        sup_raw = data.get("suppressed")
        sc_raw = data.get("suppressed_count")
        sup_bad = False
        if "suppressed" in data and sup_raw is not None and not isinstance(sup_raw, list):
            problems.append(f"{report.name}: unexpected suppressed findings")
            sup_bad = True
        sup_list = sup_raw if isinstance(sup_raw, list) else []
        if "suppressed_count" in data and sc_raw is not None:
            if not (isinstance(sc_raw, int) and not isinstance(sc_raw, bool) and sc_raw == len(sup_list)):
                problems.append(f"{report.name}: unexpected suppressed_count ({sc_raw!r})")
                sup_bad = True
        if sup_list and not sup_bad:
            mapped_dir = report_to_dir.get(report.name)
            norm_mapped = _norm_dir(mapped_dir) if mapped_dir else ""
            if not mapped_dir or norm_mapped not in allowed_map:
                problems.append(f"{report.name}: unexpected suppressed findings for this skill folder")
            elif len(sup_list) != 1 or sc_raw != 1:
                problems.append(f"{report.name}: expected exactly 1 suppressed finding, got {len(sup_list)}")
            else:
                entry = sup_list[0]
                loc = entry.get("location") if isinstance(entry, dict) else None
                sev = _text(entry.get("severity")).lower() if isinstance(entry, dict) else ""
                start_line = loc.get("start_line") if isinstance(loc, dict) else None
                if not (
                    isinstance(entry, dict)
                    and _text(entry.get("id")) == "TT3"
                    and sev in ALLOWED_SEVERITIES
                    and isinstance(loc, dict)
                    and _text(loc.get("file")) == "scripts/m0_mcp.py"
                    and _is_line(start_line)
                    and entry.get("suppressed") is True
                    and _text(entry.get("suppression_reason"))
                ):
                    problems.append(f"{report.name}: suppressed entry does not match allowed TT3 bridge waiver")
                else:
                    bridge_errs = check_bridge(allowed_map[norm_mapped])
                    if bridge_errs:
                        problems.extend(f"{report.name}: {err}" for err in bridge_errs)
                    else:
                        print(_cmd(f"{report.name}: suppressed 1: TT3 scripts/m0_mcp.py:{start_line}"))

        issues = data.get("issues")
        if not isinstance(issues, list):
            problems.append(f"{report.name}: missing or invalid issues list")
        else:
            for issue in issues:
                if not isinstance(issue, dict):
                    problems.append(f"{report.name}: invalid issue entry")
                    continue
                sev = _text(issue.get("severity")).lower()
                rule_id = _text(issue.get("id")) or "unknown"
                if sev not in ALLOWED_SEVERITIES:
                    problems.append(f"{report.name}: [{sev or 'none'}] {rule_id} unknown severity")
                    continue
                if sev not in SEVERE:
                    continue
                loc = issue.get("location")
                loc_file = _text(loc.get("file")) if isinstance(loc, dict) else ""
                start_line = loc.get("start_line") if isinstance(loc, dict) else None
                if loc_file and _is_line(start_line):
                    exp = issue.get("explanation")
                    first = next((ln.strip() for ln in exp.splitlines() if ln.strip()), "") if isinstance(exp, str) else ""
                    tail = f" {first}" if first else ""
                    problems.append(f"{report.name}: [{sev}] {rule_id} {loc_file}:{start_line}{tail}")
                else:
                    problems.append(f"{report.name}: [{sev}] {rule_id} no file:line")

        ra = data.get("risk_assessment")
        if not isinstance(ra, dict) or not _is_num(ra.get("score")):
            problems.append(f"{report.name}: missing or invalid risk_assessment")
        else:
            ra_sev = _text(ra.get("severity")).lower()
            ra_rec = _text(ra.get("recommendation")) or "unknown"
            summary = f"{report.name}: overall risk score {ra['score']} ({ra_sev or 'none'}, {ra_rec})"
            print(_cmd(summary))
            if ra_sev not in ALLOWED_SEVERITIES:
                problems.append(f"{report.name}: [{ra_sev or 'none'}] risk_assessment unknown severity")
            elif ra_sev in SEVERE:
                problems.append(summary)

    for problem in problems:
        print(f"::error::{_cmd(problem)}")
    print(_cmd(f"{len(reports)} report(s) checked, {len(problems)} problem(s)"))
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("report_dir", nargs="?")
    ap.add_argument("--allow-suppressed", action="append", default=[])
    ns, extra = ap.parse_known_args(argv)
    if not ns.report_dir or extra:
        print(f"::error::{_cmd('usage: summarize.py <report-dir> [--allow-suppressed <dir> ...]')}")
        return 1
    return summarize_dir(pathlib.Path(ns.report_dir), ns.allow_suppressed)


if __name__ == "__main__":
    sys.exit(main())
