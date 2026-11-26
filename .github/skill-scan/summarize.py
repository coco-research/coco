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
ALLOWED_IMPORTS_BRIDGE = {
    "__future__", "json", "os", "sys", "urllib", "urllib.error", "urllib.parse",
    "urllib.request", "pathlib", "m0_server",
}
ALLOWED_IMPORTS_SERVER = {
    "__future__", "argparse", "hashlib", "json", "os", "sqlite3", "sys",
    "tempfile", "datetime", "http.server", "pathlib", "urllib.parse",
}
ALLOWED_FROM_BRIDGE = {
    "__future__": {"annotations"},
    "pathlib": {"Path"},
}
ALLOWED_FROM_SERVER = {
    "__future__": {"annotations"},
    "datetime": {"datetime", "timezone"},
    "http.server": {"BaseHTTPRequestHandler", "ThreadingHTTPServer"},
    "pathlib": {"Path"},
    "urllib.parse": {"parse_qs", "urlparse"},
}
ALLOWED_DUNDER_ATTRS = {"__name__", "__init__"}
BARE_MODULE_NAMES = {"os", "sys", "urllib"}
ENV_ATTRS = {"environ", "environb", "getenv", "getenvb", "putenv", "unsetenv"}
FORBIDDEN_BUILTIN_NAMES = {
    "getattr", "vars", "globals", "locals", "compile",
    "__import__", "__builtins__", "eval", "exec",
}
FORBIDDEN_ATTR_CALLS = {
    "__import__", "exec", "eval", "import_module", "system", "popen", "create_connection",
}
FORBIDDEN_ATTRS = {"format", "format_map"}


def _is_forbidden_os_attr(attr: str) -> bool:
    return attr in {"system", "popen", "fork", "forkpty"} or attr.startswith(("exec", "spawn", "posix_spawn"))


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


def _check_common(
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
    prefix: str,
    allowed_imports: set[str],
    allowed_from: dict[str, set[str]],
) -> list[str]:
    errs: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                top = mod.split(".", 1)[0]
                if alias.asname:
                    errs.append(f"{prefix}: disallowed import alias {mod} as {alias.asname}")
                if mod not in allowed_imports or top not in allowed_imports:
                    errs.append(f"{prefix}: disallowed import {mod}")
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                errs.append(f"{prefix}: disallowed relative import")
            else:
                mod = node.module or ""
                allowed_names = allowed_from.get(mod)
                for alias in node.names:
                    if alias.asname:
                        errs.append(f"{prefix}: disallowed import alias {mod}.{alias.name} as {alias.asname}")
                if allowed_names is None:
                    errs.append(f"{prefix}: disallowed from-import {mod}")
                else:
                    for alias in node.names:
                        if alias.name not in allowed_names:
                            errs.append(f"{prefix}: disallowed from-import {mod}.{alias.name}")
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in FORBIDDEN_BUILTIN_NAMES:
                errs.append(f"{prefix}: forbidden name {node.id}")
            elif node.id in BARE_MODULE_NAMES:
                p = parents.get(node)
                if not (isinstance(p, ast.Attribute) and p.value is node):
                    errs.append(f"{prefix}: bare module reference {node.id}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_ATTR_CALLS:
                errs.append(f"{prefix}: forbidden call .{node.func.attr}")
        elif isinstance(node, ast.Attribute):
            if (
                node.attr.startswith("__")
                and node.attr.endswith("__")
                and len(node.attr) >= 4
                and node.attr not in ALLOWED_DUNDER_ATTRS
            ):
                errs.append(f"{prefix}: forbidden dunder attribute {node.attr}")
            elif node.attr in FORBIDDEN_ATTRS:
                errs.append(f"{prefix}: forbidden attribute {node.attr}")
            elif node.attr == "modules" and isinstance(node.value, ast.Name) and node.value.id == "sys":
                errs.append(f"{prefix}: forbidden attribute sys.modules")
            elif isinstance(node.value, ast.Name) and node.value.id == "os" and _is_forbidden_os_attr(node.attr):
                errs.append(f"{prefix}: forbidden os attribute os.{node.attr}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in ENV_ATTRS:
            errs.append(f"{prefix}: forbidden env string constant {node.value!r}")
    return errs


ALLOWED_SYS_PATH_DUMP = ast.dump(
    ast.parse("sys.path.insert(0, str(Path(__file__).resolve().parent))", mode="eval").body
)


def _check_sys_path(
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
    prefix: str,
    is_bridge: bool,
) -> list[str]:
    errs: list[str] = []
    ok_calls = 0
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "path"
            and isinstance(node.value, ast.Name)
            and node.value.id == "sys"
        ):
            if is_bridge:
                p = parents.get(node)
                gp = parents.get(p) if isinstance(p, ast.Attribute) and p.value is node and p.attr == "insert" else None
                if isinstance(gp, ast.Call) and gp.func is p and ast.dump(gp) == ALLOWED_SYS_PATH_DUMP:
                    ok_calls += 1
                    if ok_calls <= 1:
                        continue
            errs.append(f"{prefix}: sys.path use outside the reviewed insert")
    return errs


def _check_env(
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
    prefix: str,
    allowed_keys: set[str] | None,
) -> tuple[list[str], list[ast.Call]]:
    errs: list[str] = []
    transport_calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ENV_ATTRS:
            if node.attr == "environ" and isinstance(node.value, ast.Name) and node.value.id == "os":
                p = parents.get(node)
                gp = parents.get(p) if isinstance(p, ast.Attribute) and p.value is node and p.attr == "get" else None
                if isinstance(gp, ast.Call) and gp.func is p and 1 <= len(gp.args) <= 2 and not gp.keywords:
                    key = _str_const(gp.args[0])
                    if key is None:
                        errs.append(f"{prefix}: non-literal env key")
                    elif DENY_ENV_RE.search(key):
                        errs.append(f"{prefix}: credential-named env key {key}")
                    elif allowed_keys is not None and key not in allowed_keys:
                        errs.append(f"{prefix}: disallowed env key {key}")
                    elif key == "M0_MCP_TRANSPORT":
                        transport_calls.append(gp)
                    continue
            errs.append(f"{prefix}: disallowed env reference .{node.attr}")
        elif isinstance(node, ast.Name) and node.id in ENV_ATTRS:
            errs.append(f"{prefix}: disallowed env name {node.id}")
    return errs, transport_calls


def _check_bridge_file(path: pathlib.Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return [f"bridge check: cannot parse {path.name} ({exc})"]

    parents = _parent_map(tree)
    errs = _check_common(tree, parents, "bridge check", ALLOWED_IMPORTS_BRIDGE, ALLOWED_FROM_BRIDGE)
    errs.extend(_check_sys_path(tree, parents, "bridge check", True))
    env_errs, transport_calls = _check_env(tree, parents, "bridge check", ALLOWED_BRIDGE_ENV)
    errs.extend(env_errs)
    urlopen_calls = 0

    for node in ast.walk(tree):
        if (
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
    rel = path.relative_to(scripts_dir).as_posix()
    is_m0_server = path.parent == scripts_dir and path.name == "m0_server.py"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return [f"sibling check ({rel}): cannot parse ({exc})"]

    prefix = f"sibling check ({rel})"
    parents = _parent_map(tree)
    allowed_imports = ALLOWED_IMPORTS_SERVER if is_m0_server else set()
    allowed_from = ALLOWED_FROM_SERVER if is_m0_server else {}
    errs = _check_common(tree, parents, prefix, allowed_imports, allowed_from)
    errs.extend(_check_sys_path(tree, parents, prefix, False))
    env_errs, _ = _check_env(tree, parents, prefix, None)
    errs.extend(env_errs)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "request" and isinstance(node.value, ast.Name) and node.value.id == "urllib":
            errs.append(f"{prefix}: forbidden urllib.request reference")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"system", "popen"}:
                errs.append(f"{prefix}: forbidden call {node.func.id}")
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "connect"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "socket"
            ):
                errs.append(f"{prefix}: forbidden call socket.connect")
    return errs


# ponytail: 1 file, 1 rule, 4 request vars plus 1 transport selector. A PR can edit this file or summarize.py; kernel-owner review of any change under .github/skill-scan/** is the control. Upgrade path: per-sink taint tracking upstream, or a typed config module in the bridge.
# ponytail: values returned from sibling modules aren't traced into m0_mcp.py's Request; the shield is that no sibling can read a credential-named or unreadable env key, and none has an outbound path. Upgrade path: an inter-module taint pass, or a named allow-list per sibling (option a) if a sibling ever needs a secret. a new import in the m0 scripts needs a gate change.
# ponytail: static AST check; determined obfuscation in Python can still get past it. The backstop is the R3 human read of any diff touching waived files.
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
