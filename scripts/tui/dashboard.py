#!/usr/bin/env python3
"""CoCo TUI Dashboard v5 — Simple clear+print loop.

No Rich Live, no Layout, no Columns. Just console.clear() + console.print().
Dead simple. Always works.

Press Ctrl+C to quit.
"""

import os
import sys
import sqlite3
import subprocess
import threading
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

# ─── Constants ───────────────────────────────────────────────────────────────

HUB_DB = Path.home() / ".hub" / "hub.db"

AUTOMATED_SENDERS = [
    "anti-spam", "quarantine", "sharepoint", "zoom", "miro team",
    "jira", "confluence", "slack", "noreply", "no-reply", "newsletter",
    "notification", "mailer-daemon", "postmaster", "servicenow",
    "service now", "box.com", "grp_", "risk tech initiatives",
    "headspace", "lyft", "uber", "indeed", "linkedin",
    "github", "gitlab", "bitbucket", "aws", "amazon web services",
    "google cloud", "azure", "microsoft 365", "office 365",
    "docusign", "adobe", "okta", "duo", "sso", "security alert",
    "wendy miller",
]

INVITE_KEYWORDS = ["invite", "invitation", "rsvp", "you're invited", "calendar event", "meeting request"]

ABBREVS = {
    "AuditBoard (AB1)": "AB1", "AuditBoard Tax (AB2)": "AB2",
    "Anti-Corruption (ACC)": "ACC", "Regulatory Compliance (Reg COE)": "RegCOE",
    "Optimize (TP Inventory)": "Optim", "Cross Risk Internal (TCRE)": "TCRE",
    "Knowledge Hub": "KH", "Project Coco": "CoCo",
    "Centralizing Magnit/Aravo/OT (892)": "892",
    "Diligence COE": "DilCOE", "Ethics": "Ethics", "Privacy": "Privacy",
    "Personal Investment Compliance": "PIC",
}

def _ab(name):
    if not name: return "General"
    return ABBREVS.get(name, name[:10])

def _tr(s, n):
    if not s: return ""
    return s if len(s) <= n else s[:n-1] + "…"

def _bar(done, total, w=20):
    if total == 0: return "[" + "." * w + "]"
    f = min(w, int(w * done / total))
    return "[" + "=" * f + "." * (w - f) + "]"


# ─── Data Collectors ─────────────────────────────────────────────────────────

def run_applescript(script, timeout=30):
    try:
        return subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception:
        return ""

def collect_kh():
    if not HUB_DB.exists():
        return {}
    try:
        conn = sqlite3.connect(f"file:{HUB_DB}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        projects = [dict(r) for r in conn.execute("""
            SELECT p.id, p.name, COUNT(pc.content_id) as total
            FROM projects p LEFT JOIN project_content pc ON p.id=pc.project_id
            WHERE p.active=1 GROUP BY p.id ORDER BY total DESC
        """).fetchall()]
        todos = [dict(r) for r in conn.execute("""
            SELECT t.*, p.name as pname FROM todos t
            LEFT JOIN projects p ON t.project_id=p.id
            ORDER BY CASE t.priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, t.created_at DESC
        """).fetchall()]
        syncs = {r["source_name"]: r["last_success"] for r in conn.execute("SELECT source_name, last_success FROM sync_state")}
        conn.close()
        return {"projects": projects, "todos": todos, "syncs": syncs}
    except Exception:
        return {}

def collect_calendar():
    raw = run_applescript('''tell application "Microsoft Outlook"
  set today to current date
  set time of today to 0
  set endDate to today + (2 * days)
  set calEvents to every calendar event whose start time >= today and start time < endDate
  set output to ""
  repeat with evt in calEvents
    set evtSubject to subject of evt
    set evtStart to start time of evt
    set evtEnd to end time of evt
    try
      set evtStatus to free busy status of evt
    on error
      set evtStatus to "unknown"
    end try
    set output to output & evtSubject & "|||" & (evtStart as string) & "|||" & (evtEnd as string) & "|||" & (evtStatus as string) & linefeed
  end repeat
  return output
end tell''', timeout=45)
    if not raw: return []
    events = []
    for line in raw.strip().split("\n"):
        parts = line.strip().split("|||")
        if len(parts) < 4: continue
        start = _pd(parts[1].strip())
        if not start: continue
        events.append({"subject": parts[0].strip(), "start": start,
                        "end": _pd(parts[2].strip()), "status": parts[3].strip().lower(),
                        "cancelled": parts[0].strip().lower().startswith("canceled:")})
    events.sort(key=lambda e: e["start"])
    return events

def collect_emails():
    raw = run_applescript('''tell application "Microsoft Outlook"
  set unreadMsgs to (every message of inbox whose is read is false)
  set msgCount to count of unreadMsgs
  set output to "COUNT:" & msgCount & linefeed
  set lim to 30
  if msgCount < lim then set lim to msgCount
  repeat with i from 1 to lim
    set msg to item i of unreadMsgs
    set msgSubject to subject of msg
    set msgSender to ""
    try
      set senderObj to sender of msg
      set msgSender to name of senderObj
    end try
    set output to output & msgSender & "|||" & msgSubject & linefeed
  end repeat
  return output
end tell''', timeout=45)
    if not raw: return {"count": 0, "people": [], "automated": [], "invites": []}
    lines = raw.strip().split("\n")
    total = 0
    people, automated, invites = [], [], []
    for line in lines:
        line = line.strip()
        if line.startswith("COUNT:"):
            try: total = int(line.split(":")[1])
            except: pass
            continue
        if "|||" not in line: continue
        parts = line.split("|||")
        if len(parts) < 2: continue
        sender, subject = parts[0].strip(), parts[1].strip()
        sl, xl = sender.lower(), subject.lower()
        cat = "people"
        for kw in INVITE_KEYWORDS:
            if kw in xl: cat = "invite"; break
        if cat == "people":
            for p in AUTOMATED_SENDERS:
                if p in sl: cat = "automated"; break
        entry = {"sender": sender, "subject": subject}
        if cat == "invite": invites.append(entry)
        elif cat == "automated": automated.append(entry)
        else: people.append(entry)
    return {"count": total, "people": people, "automated": automated, "invites": invites}

def _pd(s):
    for fmt in ["%A, %B %d, %Y at %I:%M:%S %p", "%A, %B %d, %Y at %H:%M:%S"]:
        try: return datetime.strptime(s, fmt)
        except: continue
    return None


# ─── Render ──────────────────────────────────────────────────────────────────

def render_dashboard(console, kh, cal, emails):
    """Print the entire dashboard to console."""
    now = datetime.now()
    w = console.width

    # ── Header ──
    console.print()
    console.print("  [bold cyan]██████╗ ██████╗  ██████╗ ██████╗[/]")
    console.print(f" [bold cyan]██╔════╝██╔═══██╗██╔════╝██╔═══██╗[/]   [bold white]Rijul's Brain · v1.0[/]          [dim]{now.strftime('%Y-%m-%d · %-I:%M %p')}[/]")
    console.print(" [bold cyan]██║     ██║   ██║██║     ██║   ██║[/]   [dim italic][q] quit  [r] refresh[/]")
    console.print(" [bold cyan]╚██████╗╚██████╔╝╚██████╗╚██████╔╝[/]")
    console.print("  [bold cyan]╚═════╝ ╚═════╝  ╚═════╝ ╚═════╝[/]")

    projects = kh.get("projects", [])
    todos = kh.get("todos", [])
    syncs = kh.get("syncs", {})

    # ── Sync Health + Attention ──
    health = Text("  ")
    for src in ["email", "voice", "jira", "confluence"]:
        ts = syncs.get(src, "")
        label = src[:5].title()
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("+00:00", "").replace("Z", ""))
                mins = int((now - dt).total_seconds() / 60)
                if mins < 60: health.append(f"{label} 🟢 ", style="green")
                elif mins < 1440: health.append(f"{label} 🟡 ", style="yellow")
                else: health.append(f"{label} 🔴 ", style="red")
            except: health.append(f"{label} ⚫ ", style="dim")
        else:
            health.append(f"{label} ⚫ ", style="dim")

    urgent = sum(1 for t in todos if t["status"] == "open" and t["priority"] == "high")
    total_open = sum(1 for t in todos if t["status"] == "open")
    health.append("  │  ", style="dim")
    if urgent: health.append(f"🔴 {urgent} URGENT  ", style="bold red")
    health.append(f"📧 {emails.get('count', 0)} unread  ", style="white")
    health.append(f"📋 {total_open} open todos", style="dim")
    console.print(health)
    console.print()

    # ── Project Progress ──
    console.print("[bold cyan]─── PROJECT PROGRESS ─" + "─" * (w - 23) + "[/]")
    by_proj_todos = defaultdict(lambda: defaultdict(int))
    for t in todos:
        pid = t.get("project_id") or "_none"
        by_proj_todos[pid][t["status"]] += 1

    for p in projects[:8]:
        pid = p["id"]
        counts = by_proj_todos.get(pid, {})
        total = sum(counts.values())
        if total == 0 and p["total"] < 3: continue
        done = counts.get("done", 0) + counts.get("dismissed", 0) + counts.get("jira-created", 0)
        opn = counts.get("open", 0)
        pct = int(100 * done / total) if total > 0 else 0
        bar = _bar(done, total)
        name = _ab(p["name"])
        console.print(f"  [bold]{name:<10}[/] [cyan]{bar}[/]   [cyan]{done}/{total}[/] ({pct}%)   [yellow]{opn} active[/]   [dim]{p['total']} items[/]")
    console.print()

    # ── Today's Focus (3-column table) ──
    console.print("[bold cyan]─── TODAY'S FOCUS ─" + "─" * (w - 21) + "[/]")

    by_proj = defaultdict(list)
    for t in todos:
        if t["status"] == "open" and t["priority"] in ("high", "medium"):
            by_proj[t.get("pname") or "(unassigned)"].append(t)

    sorted_projs = sorted(by_proj.items(), key=lambda x: (-sum(1 for i in x[1] if i["priority"] == "high"), -len(x[1])))

    # Distribute into 3 columns
    cols = [[], [], []]
    for i, (pname, items) in enumerate(sorted_projs):
        col = cols[i % 3]
        col.append(f"[bold underline]{_ab(pname)}[/]")
        for item in items[:6]:
            title = _tr(item["title"], 40)
            if item["priority"] == "high":
                col.append(f"  [bold red]!![/] {title}")
            else:
                col.append(f"  [yellow]..[/] {title}")
        if len(items) > 6:
            col.append(f"  [dim]+{len(items)-6} more[/]")
        col.append("")

    # Render as a table with 3 columns
    tbl = Table(box=box.SIMPLE, show_header=False, expand=True, padding=(0, 1))
    tbl.add_column(ratio=1)
    tbl.add_column(ratio=1)
    tbl.add_column(ratio=1)
    max_rows = max(len(c) for c in cols) if cols[0] else 0
    for r in range(max_rows):
        tbl.add_row(
            cols[0][r] if r < len(cols[0]) else "",
            cols[1][r] if r < len(cols[1]) else "",
            cols[2][r] if r < len(cols[2]) else "",
        )
    console.print(tbl)

    # ── Tasks ──
    console.print("[bold cyan]─── TASKS ─" + "─" * (w - 13) + "[/]")

    high = sum(1 for t in todos if t["status"] == "open" and t["priority"] == "high")
    med = sum(1 for t in todos if t["status"] == "open" and t["priority"] == "medium")
    done_count = sum(1 for t in todos if t["status"] == "done")
    badge = Text("  ")
    if high: badge.append(f" {high} URGENT ", style="bold white on red"); badge.append("  ")
    if med: badge.append(f" {med} TODO ", style="bold black on yellow"); badge.append("  ")
    if done_count: badge.append(f" {done_count} DONE ", style="bold white on green"); badge.append("  ")
    badge.append(f"{total_open} open", style="dim")
    console.print(badge)
    console.print()

    by_proj_open = defaultdict(list)
    for t in todos:
        if t["status"] == "open":
            by_proj_open[t.get("pname") or "(unassigned)"].append(t)

    sorted_task_projs = sorted(by_proj_open.items(), key=lambda x: -len(x[1]))

    tcols = [[], [], []]
    for i, (pname, items) in enumerate(sorted_task_projs):
        col = tcols[i % 3]
        col.append(f"[bold underline]{_ab(pname)}[/] [dim]({len(items)} open)[/]")
        for item in items[:4]:
            title = _tr(item["title"], 38)
            if item["priority"] == "high":
                col.append(f"  [bold red]URG[/]  {title}")
            elif item["priority"] == "medium":
                col.append(f"  [yellow]TODO[/] {title}")
            else:
                col.append(f"  [green]CHK[/]  {title}")
        if len(items) > 4:
            col.append(f"  [dim]... +{len(items)-4} more[/]")
        col.append("")

    ttbl = Table(box=box.SIMPLE, show_header=False, expand=True, padding=(0, 1))
    ttbl.add_column(ratio=1)
    ttbl.add_column(ratio=1)
    ttbl.add_column(ratio=1)
    max_trows = max(len(c) for c in tcols) if tcols[0] else 0
    for r in range(max_trows):
        ttbl.add_row(
            tcols[0][r] if r < len(tcols[0]) else "",
            tcols[1][r] if r < len(tcols[1]) else "",
            tcols[2][r] if r < len(tcols[2]) else "",
        )
    console.print(ttbl)

    # ── Calendar + Emails (side by side table) ──
    console.print("[bold cyan]─── CALENDAR ─" + "─" * (w // 2 - 16) + "[/]" +
                  "  [bold yellow]─── EMAILS ─" + "─" * (w // 2 - 14) + "[/]")

    # Calendar text
    cal_lines = []
    if not cal:
        cal_lines.append("[dim]Outlook not running[/]")
    else:
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # Starting soon / now
        for evt in cal:
            if evt["cancelled"]: continue
            delta = (evt["start"] - now).total_seconds()
            if 0 < delta <= 900:
                cal_lines.append(f"[bold red]! STARTING SOON[/]  {_tr(evt['subject'], 30)}  [red]in {int(delta/60)}m[/]")
                break
            if evt["start"] <= now and evt["end"] and evt["end"] > now:
                cal_lines.append(f"[bold red]● NOW[/]  {_tr(evt['subject'], 30)}")
                break

        cal_lines.append(f"[bold underline]TODAY — {now.strftime('%A, %B %d')}[/]")
        for evt in cal[:12]:
            if evt["start"].date() != today.date(): continue
            t = evt["start"].strftime("%-I:%M") + "-" + (evt["end"].strftime("%-I:%M %p") if evt["end"] else "")
            subj = _tr(evt["subject"], 28)
            if evt["cancelled"]:
                cal_lines.append(f"  [dim strike]x {t:<16}{subj}[/]")
            elif evt["status"] == "free":
                cal_lines.append(f"  [dim]○ {t:<16}{subj}[/]")
            elif evt["status"] == "tentative":
                cal_lines.append(f"  [yellow]?[/] {t:<16}{subj}")
            else:
                cal_lines.append(f"  [green]✓[/] {t:<16}{subj}")

    # Email text
    em_lines = []
    count = emails.get("count", 0)
    people = emails.get("people", [])
    automated = emails.get("automated", [])
    invites = emails.get("invites", [])
    if count == 0:
        em_lines.append("[dim]No unread[/]")
    else:
        em_lines.append(f"[bold]PEOPLE ({len(people)})[/]")
        for e in people[:8]:
            em_lines.append(f"  [bold]{_tr(e['sender'], 18):<20}[/] {_tr(e['subject'], 30)}")
        if len(people) > 8:
            em_lines.append(f"  [dim]+{len(people)-8} more[/]")
        if invites:
            em_lines.append(f"\n[yellow]INVITES ({len(invites)})[/]")
            for e in invites[:3]:
                em_lines.append(f"  [yellow]{_tr(e['sender'], 18):<20}[/] {_tr(e['subject'], 30)}")
        if automated:
            em_lines.append(f"\n[dim]AUTOMATED ({len(automated)})[/]")

    btbl = Table(box=box.SIMPLE, show_header=False, expand=True, padding=(0, 1))
    btbl.add_column(ratio=1)
    btbl.add_column(ratio=1)
    max_brows = max(len(cal_lines), len(em_lines))
    for r in range(max_brows):
        btbl.add_row(
            cal_lines[r] if r < len(cal_lines) else "",
            em_lines[r] if r < len(em_lines) else "",
        )
    console.print(btbl)


# ─── Main Loop ───────────────────────────────────────────────────────────────

def main():
    console = Console()
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

    # Shared data with lock
    lock = threading.Lock()
    data = {"kh": {}, "cal": [], "emails": {"count": 0, "people": [], "automated": [], "invites": []}}

    def refresh_kh():
        d = collect_kh()
        with lock:
            data["kh"] = d

    def refresh_outlook():
        c = collect_calendar()
        e = collect_emails()
        with lock:
            data["cal"] = c
            data["emails"] = e

    def bg_loop():
        refresh_kh()
        refresh_outlook()
        last_kh = time.time()
        last_ol = time.time()
        while True:
            time.sleep(5)
            now = time.time()
            if now - last_kh > 120:
                refresh_kh()
                last_kh = now
            if now - last_ol > 300:
                refresh_outlook()
                last_ol = now

    # Start background thread
    t = threading.Thread(target=bg_loop, daemon=True)
    t.start()

    # Wait for first data load
    for _ in range(100):
        with lock:
            if data["kh"]:
                break
        time.sleep(0.1)

    # Main render loop — clear and print every 2 seconds
    try:
        while True:
            with lock:
                kh = data["kh"]
                cal = data["cal"]
                emails = data["emails"]

            console.clear()
            try:
                render_dashboard(console, kh, cal, emails)
            except Exception as e:
                console.print(f"[red]Render error: {e}[/]")

            time.sleep(2)
    except KeyboardInterrupt:
        pass

    console.clear()
    console.print("[dim]CoCo dashboard stopped.[/]")


if __name__ == "__main__":
    main()
