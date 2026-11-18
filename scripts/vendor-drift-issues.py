#!/usr/bin/env python3
"""Open or update one GitHub issue per drifted row from scripts/vendor-check.py --json.

Report-only helper for .github/workflows/vendor-drift.yml:
- Ensures the `vendor-drift` label exists.
- Opens or updates one issue per row with status == "drift", titled `<name>: <pinned> → <new_ref>`.
- Never opens pull requests and never runs git push.
"""
# ponytail: ceiling = sequential gh CLI calls for ~20 lock rows; upgrade path = GraphQL batch mutation past 100 rows.

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

LABEL = "vendor-drift"


def marker_for(name):
    return f"<!-- vendor-drift-item: {name} -->"


def render_issue(name, pinned, repo_url, row):
    new_ref = str(row.get("new_ref") or "").strip()
    changed_files = int(row.get("changed_files") or 0)
    licence_changed = bool(row.get("licence_changed"))
    risky_lines = int(row.get("risky_lines") or 0)
    title = f"{name}: {pinned} \u2192 {new_ref}"
    body = "\n".join([
        marker_for(name),
        f"Upstream drift detected for vendored entry `{name}` ({repo_url}).",
        "",
        f"- **Pinned ref:** `{pinned}`",
        f"- **New upstream ref:** `{new_ref}`",
        f"- **`changed_files`:** `{changed_files}`",
        f"- **`licence_changed`:** `{str(licence_changed).lower()}`",
        f"- **`risky_lines`:** `{risky_lines}`",
        "",
        "Report-only check: review the upstream diff and licence files manually before updating `data/vendor-lock.json`.",
        "",
    ])
    return title, body


def run_gh(args):
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(f"vendor-drift-issues: gh {' '.join(args[:2])} failed: {proc.stderr.strip()}\n")
        raise SystemExit(1)
    return proc.stdout


def find_existing_issue(open_issues, name):
    needle = marker_for(name)
    prefix = f"{name}: "
    for issue in open_issues:
        body = issue.get("body") or ""
        title = issue.get("title") or ""
        if needle in body or title.startswith(prefix):
            return issue
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sync vendor-drift GitHub issues from vendor-check JSON.")
    ap.add_argument("--lock", default="data/vendor-lock.json")
    ap.add_argument("--report", required=True, help="JSON output from scripts/vendor-check.py --json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    lock_rows = json.loads(pathlib.Path(args.lock).read_text(encoding="utf-8"))
    report_rows = json.loads(pathlib.Path(args.report).read_text(encoding="utf-8"))
    lock_by_name = {
        str(r["name"]).strip(): r
        for r in lock_rows
        if isinstance(r, dict) and isinstance(r.get("name"), str)
    }

    drifted = [r for r in report_rows if isinstance(r, dict) and r.get("status") == "drift"]
    licence_changes = sum(1 for r in drifted if r.get("licence_changed"))

    if not drifted:
        print("vendor drift: 0 issues · 0 licence changes")
        return 0

    open_issues = []
    if not args.dry_run:
        run_gh([
            "label", "create", LABEL,
            "--description", "Upstream drift in vendored assets",
            "--color", "D93F0B",
            "--force",
        ])
        raw_list = run_gh([
            "issue", "list",
            "--label", LABEL,
            "--state", "open",
            "--limit", "200",
            "--json", "number,title,body",
        ])
        open_issues = json.loads(raw_list or "[]")

    summaries = []
    for row in drifted:
        name = str(row.get("name") or "").strip()
        lock_entry = lock_by_name.get(name, {})
        pinned = str(lock_entry.get("pinned_ref") or "unknown").strip()
        repo_url = str(lock_entry.get("repo") or "").strip()
        new_ref = str(row.get("new_ref") or "").strip()
        title, body = render_issue(name, pinned, repo_url, row)
        summaries.append(f"{name} {pinned} \u2192 {new_ref}")

        if args.dry_run:
            continue

        existing = find_existing_issue(open_issues, name)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as tf:
            tf.write(body)
            body_path = pathlib.Path(tf.name)
        try:
            if existing is not None:
                if existing.get("title") != title or (existing.get("body") or "") != body:
                    run_gh([
                        "issue", "edit", str(existing["number"]),
                        "--title", title,
                        "--body-file", str(body_path),
                    ])
            else:
                run_gh([
                    "issue", "create",
                    "--label", LABEL,
                    "--title", title,
                    "--body-file", str(body_path),
                ])
        finally:
            body_path.unlink(missing_ok=True)

    noun = "issue" if len(summaries) == 1 else "issues"
    print(f"vendor drift: {len(summaries)} {noun} ({', '.join(summaries)}) · {licence_changes} licence changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
