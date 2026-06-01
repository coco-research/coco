"""Self-improvement cycle orchestrator.

Manages the 10-agent product squad that analyzes the CoCo Platform codebase,
identifies improvements, builds them in isolated git worktrees, tests, reviews,
and presents them to a human for approval.
"""

import json
import os
import shutil
import subprocess
import uuid
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

import structlog

from app.db.session import get_db
from app.services.event_bus import event_bus
from app.services.process_manager import process_manager
from app.services.verification import verification_service
from app.services.worktree_manager import WorktreeManager, DENYLIST_PATTERNS

log = structlog.get_logger()

REPO_ROOT = Path(__file__).parent.parent.parent.parent  # coco-platform root
LOCK_FILE = Path.home() / ".coco" / "self_improve.lock"
MIN_DISK_MB = 500  # minimum free disk space in MB

# Valid cycle statuses
CYCLE_STATUSES = [
    "idle", "planning", "architecting", "developing", "testing",
    "reviewing", "documenting", "awaiting_approval", "merging",
    "integrating", "completed", "rejected", "failed",
]

# Valid improvement statuses
IMPROVEMENT_STATUSES = [
    "proposed", "approved", "in_progress", "testing", "review",
    "documenting", "awaiting_approval", "approved_by_human",
    "rejected_by_human", "merged", "failed",
]

# Squad role definitions with prompt templates
SQUAD_ROLES = {
    "pm": {
        "name": "PM Agent",
        "stage": "planning",
        "model": "opus",
        "prompt_template": (
            "You are a PM analyzing the CoCo Platform codebase at {repo_root}. "
            "Read the .planning/ docs, recent git log (last 20 commits), and source code structure. "
            "Identify the top {max_improvements} improvements ranked by impact. "
            "{focus_clause}"
            "For each improvement, output a JSON array where each item has these fields: "
            "title (string), description (string), priority (int, 1=highest), "
            "category (one of: performance, ux, tests, refactor, feature, docs), "
            "estimated_files (list of file paths that would change). "
            "Output ONLY the JSON array, no other text. Do NOT modify any files."
        ),
    },
    "architect": {
        "name": "Architect Agent",
        "stage": "architecting",
        "model": "opus",
        "prompt_template": (
            "You are a software architect reviewing proposed improvements for CoCo Platform at {repo_root}. "
            "Here are the proposed improvements:\n{improvements_json}\n\n"
            "For each improvement: validate feasibility by checking if the estimated files exist, "
            "check for dependency conflicts between improvements (two improvements changing the same files), "
            "and suggest an optimal build order. "
            "Output a JSON array with the same items, reordered by build sequence, with an added field "
            "'build_order' (int) and 'architect_notes' (string). Remove any infeasible improvements. "
            "Output ONLY the JSON array, no other text. Do NOT modify any files."
        ),
    },
    "developer": {
        "name": "Developer Agent",
        "stage": "developing",
        "model": "opus",
        "prompt_template": (
            "You are working in a git worktree at {worktree_path} on branch {branch_name}. "
            "Implement this improvement:\n\nTitle: {title}\nDescription: {description}\n\n"
            "IMPORTANT SAFETY RULES:\n"
            "- Do NOT modify any files matching these patterns: {denylist}\n"
            "- Do NOT modify any .db files, .env files, or credentials\n"
            "- Work ONLY within the worktree directory\n\n"
            "Make your changes, then commit with a descriptive message prefixed with 'self-improve: '. "
            "When done, output a JSON object with: "
            "files_changed (list of paths), summary (string describing what changed). "
            "Output ONLY the JSON, no other text."
        ),
    },
    "tester": {
        "name": "Tester Agent",
        "stage": "testing",
        "model": "sonnet",
        "prompt_template": (
            "You are testing changes in the worktree at {worktree_path} on branch {branch_name}. "
            "Run the test suite: cd {worktree_path} && python -m pytest backend/ --tb=short -q "
            "Also check for type errors and linting issues. "
            "Report results as a JSON object with: "
            "passed (int), failed (int), errors (int), output (string with test output). "
            "Output ONLY the JSON, no other text."
        ),
    },
    "security": {
        "name": "Security Agent",
        "stage": "testing",
        "model": "sonnet",
        "prompt_template": (
            "You are a security scanner reviewing changes in branch {branch_name} of the CoCo Platform at {repo_root}. "
            "Run: git diff main...{branch_name}\n\n"
            "Check the diff for:\n"
            "1) Files matching denylist patterns (VIOLATION if found): {denylist}\n"
            "2) Hardcoded secrets, API keys, tokens, or passwords\n"
            "3) SQL injection risks (string formatting in SQL queries instead of parameterized)\n"
            "4) XSS vulnerabilities in any frontend code\n"
            "5) Unsafe file operations (path traversal, arbitrary file reads/writes)\n\n"
            "Report as JSON: {{\"passed\": bool, \"issues\": [\"description of each issue\"]}}. "
            "Output ONLY the JSON, no other text."
        ),
    },
    "reviewer": {
        "name": "Reviewer Agent",
        "stage": "reviewing",
        "model": "opus",
        "prompt_template": (
            "You are reviewing code changes for the CoCo Platform. "
            "Review this diff:\n\n{diff}\n\n"
            "Check for:\n"
            "- Code quality and readability\n"
            "- Adherence to existing patterns (FastAPI routers, Pydantic models, SQLite with dict(row))\n"
            "- Potential bugs or edge cases\n"
            "- Performance issues\n"
            "- Missing error handling\n\n"
            "Output a JSON object: {{\"approved\": bool, \"issues\": [\"description\"], \"suggestions\": [\"suggestion\"]}}. "
            "Output ONLY the JSON, no other text."
        ),
    },
    "doc-writer": {
        "name": "Doc Writer Agent",
        "stage": "documenting",
        "model": "sonnet",
        "prompt_template": (
            "Write a PR description and CHANGELOG entry for this improvement:\n\n"
            "Title: {title}\n"
            "Description: {description}\n"
            "Diff summary: {diff_stat}\n"
            "Test results: {test_results}\n"
            "Review notes: {review_notes}\n\n"
            "Output a JSON object with: "
            "pr_description (markdown string suitable for a GitHub PR body), "
            "changelog_entry (single line for CHANGELOG.md). "
            "Output ONLY the JSON, no other text."
        ),
    },
    "qa-lead": {
        "name": "QA Lead Agent",
        "stage": "integrating",
        "model": "opus",
        "prompt_template": (
            "All self-improvement changes have been merged into main at {repo_root}. "
            "Run the full test suite: cd {repo_root} && python -m pytest backend/ --tb=short -q "
            "Also run: ruff check backend/ "
            "Check for regressions and integration issues across all merged improvements. "
            "Report as JSON: {{\"all_passed\": bool, \"regressions\": [\"description\"], \"integration_issues\": [\"description\"]}}. "
            "Output ONLY the JSON, no other text."
        ),
    },
}


def _check_disk_space(min_mb: int = MIN_DISK_MB) -> bool:
    """Return True if at least ``min_mb`` MB of disk space is free."""
    try:
        usage = shutil.disk_usage(REPO_ROOT)
        free_mb = usage.free / (1024 * 1024)
        if free_mb < min_mb:
            log.warning("disk_space_low", free_mb=round(free_mb, 1), min_mb=min_mb)
            return False
        return True
    except Exception as e:
        log.warning("disk_space_check_failed", error=str(e))
        return True  # optimistic fallback


def _acquire_lock() -> bool:
    """Acquire the self-improve lock file. Returns False if another cycle owns it."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        try:
            content = LOCK_FILE.read_text().strip()
            pid = int(content.split(":")[0]) if content else 0
            # Check if the owning process is still alive
            if pid > 0:
                os.kill(pid, 0)  # signal 0 checks existence
                log.warning("lock_held_by_running_process", pid=pid)
                return False
        except (ProcessLookupError, OSError, ValueError):
            # Process is gone — stale lock, safe to take over
            log.info("removing_stale_lock", path=str(LOCK_FILE))
    LOCK_FILE.write_text(f"{os.getpid()}:{datetime.now(timezone.utc).isoformat()}")
    return True


def _release_lock():
    """Release the self-improve lock file."""
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception as e:
        log.warning("lock_release_failed", error=str(e))


def cleanup_stale_worktrees(max_age_hours: int = 24):
    """Remove self-improve worktrees older than ``max_age_hours``."""
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        if result.returncode != 0:
            log.warning("worktree_list_failed", stderr=result.stderr[:200])
            return

        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        current_worktree: str | None = None

        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                current_worktree = line[len("worktree "):]
            elif line.startswith("branch ") and current_worktree:
                branch = line[len("branch refs/heads/"):]
                if branch.startswith("self-improve/"):
                    wt_path = Path(current_worktree)
                    if wt_path.exists():
                        try:
                            mtime = datetime.fromtimestamp(wt_path.stat().st_mtime, tz=timezone.utc)
                            if mtime < cutoff:
                                log.info("cleaning_stale_worktree", path=str(wt_path), branch=branch)
                                subprocess.run(
                                    ["git", "worktree", "remove", "--force", str(wt_path)],
                                    capture_output=True, cwd=REPO_ROOT,
                                )
                                # Also try to delete the branch
                                subprocess.run(
                                    ["git", "branch", "-D", branch],
                                    capture_output=True, cwd=REPO_ROOT,
                                )
                        except Exception as e:
                            log.warning("stale_worktree_cleanup_failed", path=str(wt_path), error=str(e))
                current_worktree = None
    except Exception as e:
        log.warning("cleanup_stale_worktrees_error", error=str(e))


class SelfImproveService:
    # Non-terminal states that require a live driving process. The state
    # machine only advances while a spawned agent is alive and emitting
    # completion events, so a cycle found in one of these after a restart was
    # interrupted by a crash/restart and is dead. 'awaiting_approval' is
    # EXCLUDED — it intentionally waits for a human and survives restarts.
    _INTERRUPTED_STATES = (
        "planning", "architecting", "developing", "testing",
        "reviewing", "documenting", "merging", "integrating",
    )

    def __init__(self):
        self.worktree_mgr = WorktreeManager()
        self._active_cycle_id: str | None = None
        self._lock = threading.Lock()

    def recover_interrupted_cycles(self) -> int:
        """Fail any cycle left mid-flight by a crash/restart. Returns count.

        Call ONCE at app startup (lifespan), when nothing is driving a cycle.
        Marks every cycle stuck in a processing state as 'failed' (recording
        the reason), clears in-memory active state, and releases the lock file
        so a new cycle can start cleanly. This is what prevents a crashed cycle
        from wedging in 'planning' forever (the failure mode that left cycle
        9faac75d stuck for 24 days). Idempotent.
        """
        now = datetime.now(timezone.utc).isoformat()
        placeholders = ",".join("?" for _ in self._INTERRUPTED_STATES)
        with get_db() as db:
            rows = db.exec_driver_sql(
                f"SELECT id FROM self_improve_cycles WHERE status IN ({placeholders})",
                tuple(self._INTERRUPTED_STATES),
            ).fetchall()
            ids = [r._mapping["id"] for r in rows]
            for cid in ids:
                db.exec_driver_sql(
                    "UPDATE self_improve_cycles SET status = 'failed', "
                    "error = COALESCE(NULLIF(error, ''), ?), completed_at = ? "
                    "WHERE id = ?",
                    ("Interrupted by restart (no active driver process)", now, cid),
                )
        if ids:
            with self._lock:
                if self._active_cycle_id in ids:
                    self._active_cycle_id = None
            _release_lock()
            log.info("recovered_interrupted_cycles", count=len(ids), cycle_ids=ids)
        return len(ids)

    # ------------------------------------------------------------------
    # Cycle CRUD
    # ------------------------------------------------------------------

    def start_cycle(
        self,
        budget_usd: float,
        max_improvements: int,
        focus_areas: list[str] | None,
    ) -> dict:
        """Start a new self-improvement cycle."""
        # Pre-flight checks
        if not _check_disk_space():
            raise RuntimeError(f"Insufficient disk space (need at least {MIN_DISK_MB}MB free)")

        if not _acquire_lock():
            raise RuntimeError("Another self-improvement cycle is running (lock file held)")

        try:
            # Clean up stale worktrees from previous failed cycles
            cleanup_stale_worktrees()

            with self._lock:
                if self._active_cycle_id is not None:
                    # Check if it's actually still active in DB
                    existing = self.get_cycle(self._active_cycle_id)
                    if existing and existing.get("status") not in ("completed", "rejected", "failed"):
                        _release_lock()
                        raise RuntimeError("A self-improvement cycle is already active")
                    self._active_cycle_id = None

                cycle_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc).isoformat()

                with get_db() as db:
                    db.exec_driver_sql(
                        """INSERT INTO self_improve_cycles
                           (id, status, budget_usd, spent_usd, max_improvements, focus_areas, started_at, created_at)
                           VALUES (?, ?, ?, 0.0, ?, ?, ?, ?)""",
                        (
                            cycle_id, "planning", budget_usd, max_improvements,
                            json.dumps(focus_areas) if focus_areas else None,
                            now, now,
                        ),
                    )
                    pass  # auto-commit

                self._active_cycle_id = cycle_id
        except Exception:
            _release_lock()
            raise

        # Spawn PM agent to analyze codebase.
        #
        # CRITICAL: everything below runs *after* the lock-guarded try/except
        # above, so any failure here (prompt build, agent spawn) used to wedge
        # the cycle in 'planning' forever and leak the lock file with no error
        # recorded. Guard it: on failure, mark the cycle 'failed' (records the
        # error) and release the lock via _fail_cycle so the system is left in
        # a recoverable state and a new cycle can start.
        try:
            focus_clause = ""
            if focus_areas:
                focus_clause = f"Focus areas: {', '.join(focus_areas)}. "

            prompt = SQUAD_ROLES["pm"]["prompt_template"].format(
                repo_root=REPO_ROOT,
                max_improvements=max_improvements,
                focus_clause=focus_clause,
            )

            self._spawn_squad_agent(cycle_id, "pm", prompt)
        except Exception as e:
            log.error("start_cycle_spawn_failed", cycle_id=cycle_id, error=str(e))
            # _fail_cycle records the error, clears _active_cycle_id, and
            # releases the lock (idempotent if already released).
            self._fail_cycle(cycle_id, f"Failed to spawn PM agent: {e}")
            raise

        event_bus.emit("self_improve.cycle_started", {
            "cycle_id": cycle_id,
            "budget_usd": budget_usd,
            "max_improvements": max_improvements,
        })

        return self.get_cycle(cycle_id)

    def get_cycle(self, cycle_id: str) -> dict | None:
        """Get cycle data with improvements."""
        with get_db() as db:
            row = db.exec_driver_sql(
                "SELECT id, status, budget_usd, spent_usd, max_improvements, focus_areas, "
                "started_at, completed_at, error, created_at FROM self_improve_cycles WHERE id = ?",
                (cycle_id,),
            ).fetchone()
            if not row:
                return None
            cycle = dict(row._mapping)
            cycle["focus_areas"] = json.loads(cycle["focus_areas"]) if cycle["focus_areas"] else None

            # Get improvements
            imp_rows = db.exec_driver_sql(
                "SELECT id, cycle_id, title, description, priority, category, status, "
                "worktree_path, branch_name, diff_summary, diff_stat, test_results, "
                "review_notes, security_scan, pr_description, agent_id, human_comment, "
                "reject_reason, created_at, updated_at "
                "FROM self_improve_improvements WHERE cycle_id = ? ORDER BY priority",
                (cycle_id,),
            ).fetchall()
            improvements = []
            for imp_row in imp_rows:
                imp = dict(imp_row._mapping)
                imp["test_results"] = json.loads(imp["test_results"]) if imp["test_results"] else None
                imp["security_scan"] = json.loads(imp["security_scan"]) if imp["security_scan"] else None
                improvements.append(imp)
            cycle["improvements"] = improvements

            # Count spawned agents
            agent_count = db.exec_driver_sql(
                "SELECT COUNT(*) FROM self_improve_agents WHERE cycle_id = ?",
                (cycle_id,),
            ).fetchone()[0]
            cycle["agents_spawned"] = agent_count

            return cycle

    def list_cycles(self, limit: int = 10) -> list[dict]:
        """List recent cycles."""
        with get_db() as db:
            rows = db.exec_driver_sql(
                "SELECT id, status, budget_usd, spent_usd, max_improvements, focus_areas, "
                "started_at, completed_at, error, created_at "
                "FROM self_improve_cycles ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            cycles = []
            for row in rows:
                cycle = dict(row._mapping)
                cycle["focus_areas"] = json.loads(cycle["focus_areas"]) if cycle["focus_areas"] else None
                # Count improvements
                imp_count = db.exec_driver_sql(
                    "SELECT COUNT(*) FROM self_improve_improvements WHERE cycle_id = ?",
                    (cycle["id"],),
                ).fetchone()[0]
                cycle["improvement_count"] = imp_count
                agent_count = db.exec_driver_sql(
                    "SELECT COUNT(*) FROM self_improve_agents WHERE cycle_id = ?",
                    (cycle["id"],),
                ).fetchone()[0]
                cycle["agents_spawned"] = agent_count
                cycles.append(cycle)
            return cycles

    def get_active_cycle(self) -> dict | None:
        """Get currently running cycle, if any."""
        with get_db() as db:
            row = db.exec_driver_sql(
                "SELECT id FROM self_improve_cycles WHERE status NOT IN ('completed', 'rejected', 'failed') "
                "ORDER BY created_at DESC LIMIT 1",
            ).fetchone()
            if not row:
                return None
            return self.get_cycle(row._mapping["id"])

    def cancel_cycle(self, cycle_id: str) -> dict:
        """Cancel a running cycle, cleanup all worktrees."""
        cycle = self.get_cycle(cycle_id)
        if not cycle:
            raise ValueError("Cycle not found")

        if cycle["status"] in ("completed", "rejected", "failed"):
            raise RuntimeError(f"Cycle already in terminal state: {cycle['status']}")

        now = datetime.now(timezone.utc).isoformat()

        # Kill all running agents for this cycle
        with get_db() as db:
            agent_rows = db.exec_driver_sql(
                "SELECT agent_id FROM self_improve_agents WHERE cycle_id = ? AND status = 'running'",
                (cycle_id,),
            ).fetchall()
            for arow in agent_rows:
                aid = arow._mapping["agent_id"]
                try:
                    process_manager.kill(aid)
                except Exception as e:
                    log.warning("kill_squad_agent_failed", agent_id=aid, error=str(e))

                db.exec_driver_sql(
                    "UPDATE self_improve_agents SET status = 'cancelled', completed_at = ? WHERE agent_id = ?",
                    (now, aid),
                )

            # Cleanup all worktrees for improvements
            imp_rows = db.exec_driver_sql(
                "SELECT branch_name FROM self_improve_improvements WHERE cycle_id = ? AND branch_name IS NOT NULL",
                (cycle_id,),
            ).fetchall()
            for imp_row in imp_rows:
                try:
                    self.worktree_mgr.cleanup(imp_row._mapping["branch_name"])
                except Exception as e:
                    log.warning("cleanup_worktree_failed", branch=imp_row._mapping["branch_name"], error=str(e))

            # Update cycle status
            db.exec_driver_sql(
                "UPDATE self_improve_cycles SET status = 'failed', error = 'Cancelled by user', completed_at = ? WHERE id = ?",
                (now, cycle_id),
            )
            db.commit()

        with self._lock:
            if self._active_cycle_id == cycle_id:
                self._active_cycle_id = None

        _release_lock()
        event_bus.emit("self_improve.cycle_cancelled", {"cycle_id": cycle_id})
        return self.get_cycle(cycle_id)

    # ------------------------------------------------------------------
    # Improvement actions
    # ------------------------------------------------------------------

    def get_improvement(self, improvement_id: str) -> dict | None:
        """Get a single improvement by ID."""
        with get_db() as db:
            row = db.exec_driver_sql(
                "SELECT id, cycle_id, title, description, priority, category, status, "
                "worktree_path, branch_name, diff_summary, diff_stat, test_results, "
                "review_notes, security_scan, pr_description, agent_id, human_comment, "
                "reject_reason, created_at, updated_at "
                "FROM self_improve_improvements WHERE id = ?",
                (improvement_id,),
            ).fetchone()
            if not row:
                return None
            imp = dict(row._mapping)
            imp["test_results"] = json.loads(imp["test_results"]) if imp["test_results"] else None
            imp["security_scan"] = json.loads(imp["security_scan"]) if imp["security_scan"] else None
            return imp

    def get_improvement_diff(self, improvement_id: str) -> str | None:
        """Get full diff for an improvement."""
        imp = self.get_improvement(improvement_id)
        if not imp or not imp["branch_name"]:
            return None
        return self.worktree_mgr.get_diff(imp["branch_name"])

    def approve_improvement(self, improvement_id: str, comment: str | None = None) -> dict:
        """Human approves an improvement. Merge the worktree."""
        imp = self.get_improvement(improvement_id)
        if not imp:
            raise ValueError("Improvement not found")
        if imp["status"] != "awaiting_approval":
            raise RuntimeError(f"Improvement not awaiting approval (status: {imp['status']})")

        now = datetime.now(timezone.utc).isoformat()
        branch = imp["branch_name"]

        # Check denylist one more time
        violations = self.worktree_mgr.check_denylist(branch)
        if violations:
            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE self_improve_improvements SET status = 'failed', "
                    "reject_reason = ?, updated_at = ? WHERE id = ?",
                    (f"Denylist violations: {'; '.join(violations)}", now, improvement_id),
                )
                pass  # auto-commit
            raise RuntimeError(f"Denylist violations found: {violations}")

        # Merge
        success = self.worktree_mgr.merge(branch)
        if not success:
            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE self_improve_improvements SET status = 'failed', "
                    "reject_reason = 'Merge conflict', updated_at = ? WHERE id = ?",
                    (now, improvement_id),
                )
                pass  # auto-commit
            raise RuntimeError("Merge failed — likely a conflict")

        # Update improvement
        with get_db() as db:
            db.exec_driver_sql(
                "UPDATE self_improve_improvements SET status = 'merged', human_comment = ?, updated_at = ? WHERE id = ?",
                (comment, now, improvement_id),
            )
            db.commit()

        # Cleanup worktree
        try:
            self.worktree_mgr.cleanup(branch)
        except Exception as e:
            log.warning("cleanup_after_merge_failed", branch=branch, error=str(e))

        event_bus.emit("self_improve.improvement_merged", {
            "improvement_id": improvement_id,
            "cycle_id": imp["cycle_id"],
            "title": imp["title"],
        })

        # Check if all improvements in cycle are resolved
        self._check_all_improvements_resolved(imp["cycle_id"])

        return self.get_improvement(improvement_id)

    def reject_improvement(self, improvement_id: str, reason: str | None = None) -> dict:
        """Human rejects an improvement. Cleanup the worktree."""
        imp = self.get_improvement(improvement_id)
        if not imp:
            raise ValueError("Improvement not found")
        if imp["status"] != "awaiting_approval":
            raise RuntimeError(f"Improvement not awaiting approval (status: {imp['status']})")

        now = datetime.now(timezone.utc).isoformat()

        with get_db() as db:
            db.exec_driver_sql(
                "UPDATE self_improve_improvements SET status = 'rejected_by_human', "
                "reject_reason = ?, updated_at = ? WHERE id = ?",
                (reason, now, improvement_id),
            )
            db.commit()

        # Cleanup worktree
        if imp["branch_name"]:
            try:
                self.worktree_mgr.cleanup(imp["branch_name"])
            except Exception as e:
                log.warning("cleanup_after_reject_failed", branch=imp["branch_name"], error=str(e))

        event_bus.emit("self_improve.improvement_rejected", {
            "improvement_id": improvement_id,
            "cycle_id": imp["cycle_id"],
            "title": imp["title"],
        })

        # Check if all improvements in cycle are resolved
        self._check_all_improvements_resolved(imp["cycle_id"])

        return self.get_improvement(improvement_id)

    # ------------------------------------------------------------------
    # Agent completion handler — state machine core
    # ------------------------------------------------------------------

    def on_agent_completed(self, agent_id: str, status: str):
        """Called when a squad agent finishes. Advances the state machine."""
        with get_db() as db:
            sa_row = db.exec_driver_sql(
                "SELECT id, cycle_id, improvement_id, role FROM self_improve_agents WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()
            if not sa_row:
                return  # Not a self-improve agent

            cycle_id = sa_row._mapping["cycle_id"]
            improvement_id = sa_row._mapping["improvement_id"]
            role = sa_row._mapping["role"]
            now = datetime.now(timezone.utc).isoformat()

            # Update squad agent record
            db.exec_driver_sql(
                "UPDATE self_improve_agents SET status = ?, completed_at = ? WHERE agent_id = ?",
                (status, now, agent_id),
            )

            # Get agent output (last 200 lines)
            output_rows = db.exec_driver_sql(
                "SELECT chunk FROM agent_output WHERE agent_id = ? ORDER BY id DESC LIMIT 200",
                (agent_id,),
            ).fetchall()
            raw_output = "\n".join(r._mapping["chunk"] for r in reversed(output_rows))

            # Store summary
            db.exec_driver_sql(
                "UPDATE self_improve_agents SET output_summary = ? WHERE agent_id = ?",
                (raw_output[:5000], agent_id),
            )
            db.commit()

        if status == "failed":
            self._handle_agent_failure(cycle_id, role, improvement_id, raw_output)
            return

        # Route based on role
        try:
            if role == "pm":
                self._handle_pm_completed(cycle_id, raw_output)
            elif role == "architect":
                self._handle_architect_completed(cycle_id, raw_output)
            elif role == "developer":
                self._handle_dev_completed(cycle_id, improvement_id, raw_output)
            elif role == "tester":
                self._handle_tester_completed(cycle_id, improvement_id, raw_output)
            elif role == "security":
                self._handle_security_completed(cycle_id, improvement_id, raw_output)
            elif role == "reviewer":
                self._handle_reviewer_completed(cycle_id, improvement_id, raw_output)
            elif role == "doc-writer":
                self._handle_doc_writer_completed(cycle_id, improvement_id, raw_output)
            elif role == "qa-lead":
                self._handle_qa_lead_completed(cycle_id, raw_output)
        except Exception as e:
            log.error("state_machine_error", cycle_id=cycle_id, role=role, error=str(e))
            self._fail_cycle(cycle_id, f"State machine error in {role}: {str(e)}")

    def _handle_pm_completed(self, cycle_id: str, output: str):
        """PM completed — parse improvements, create records, spawn Architect."""
        improvements = self._parse_json_from_output(output)
        if not isinstance(improvements, list) or len(improvements) == 0:
            self._fail_cycle(cycle_id, "PM agent produced no valid improvements")
            return

        now = datetime.now(timezone.utc).isoformat()
        with get_db() as db:
            for imp in improvements:
                imp_id = str(uuid.uuid4())
                db.exec_driver_sql(
                    """INSERT INTO self_improve_improvements
                       (id, cycle_id, title, description, priority, category, status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, 'proposed', ?, ?)""",
                    (
                        imp_id, cycle_id,
                        imp.get("title", "Untitled"),
                        imp.get("description", ""),
                        imp.get("priority", 99),
                        imp.get("category", "refactor"),
                        now, now,
                    ),
                )

                # Run G1 ideation gate with retry on each proposed improvement
                try:
                    cycle_row = db.exec_driver_sql(
                        "SELECT focus_areas, budget_usd, spent_usd FROM self_improve_cycles WHERE id = ?", (cycle_id,)
                    ).fetchone()
                    focus_areas = json.loads(cycle_row._mapping["focus_areas"]) if cycle_row and cycle_row._mapping["focus_areas"] else []
                    g1_result = verification_service.run_gate_with_retry(
                        gate_name="G1_ideation",
                        input_data={"requirements": focus_areas},
                        output_data={
                            "title": imp.get("title", ""),
                            "description": imp.get("description", ""),
                            "priority": imp.get("category", ""),  # maps to priority validation
                            "category": imp.get("category", ""),
                        },
                        entity_type="improvement",
                        entity_id=imp_id,
                        max_retries=2,
                        budget_usd=cycle_row._mapping["budget_usd"] if cycle_row else None,
                        spent_usd=cycle_row._mapping["spent_usd"] if cycle_row else 0.0,
                    )
                    if g1_result.verdict.value == "fail":
                        log.warning("gate_failed", gate="G1", improvement_id=imp_id, retries=g1_result.retry_count)
                except Exception as e:
                    log.debug("g1_gate_skipped", error=str(e))

            db.exec_driver_sql(
                "UPDATE self_improve_cycles SET status = 'architecting' WHERE id = ?",
                (cycle_id,),
            )
            db.commit()

        # Spawn Architect
        improvements_json = json.dumps(improvements, indent=2)
        prompt = SQUAD_ROLES["architect"]["prompt_template"].format(
            repo_root=REPO_ROOT,
            improvements_json=improvements_json,
        )
        self._spawn_squad_agent(cycle_id, "architect", prompt)

        event_bus.emit("self_improve.stage_changed", {
            "cycle_id": cycle_id, "stage": "architecting",
            "improvements_count": len(improvements),
        })

    def _handle_architect_completed(self, cycle_id: str, output: str):
        """Architect completed — validate/reorder, spawn Devs in parallel worktrees."""
        ordered = self._parse_json_from_output(output)
        if not isinstance(ordered, list) or len(ordered) == 0:
            self._fail_cycle(cycle_id, "Architect agent produced no valid output")
            return

        now = datetime.now(timezone.utc).isoformat()
        with get_db() as db:
            # Update improvements with architect's ordering
            imp_rows = db.exec_driver_sql(
                "SELECT id, title FROM self_improve_improvements WHERE cycle_id = ? ORDER BY priority",
                (cycle_id,),
            ).fetchall()

            # Match by title
            title_to_id = {r._mapping["title"]: r._mapping["id"] for r in imp_rows}

            for item in ordered:
                imp_id = title_to_id.get(item.get("title"))
                if imp_id:
                    new_priority = item.get("build_order", item.get("priority", 99))
                    db.exec_driver_sql(
                        "UPDATE self_improve_improvements SET priority = ?, status = 'approved', updated_at = ? WHERE id = ?",
                        (new_priority, now, imp_id),
                    )

            # Get approved improvements (up to max)
            cycle_row = db.exec_driver_sql(
                "SELECT max_improvements FROM self_improve_cycles WHERE id = ?",
                (cycle_id,),
            ).fetchone()
            max_imp = cycle_row._mapping["max_improvements"] if cycle_row else 5

            approved = db.exec_driver_sql(
                "SELECT id, title, description, category FROM self_improve_improvements "
                "WHERE cycle_id = ? AND status = 'approved' ORDER BY priority LIMIT ?",
                (cycle_id, max_imp),
            ).fetchall()

            db.exec_driver_sql(
                "UPDATE self_improve_cycles SET status = 'developing' WHERE id = ?",
                (cycle_id,),
            )
            db.commit()

        # Run G2 plan gate with retry on the architect's output
        try:
            with get_db() as db:
                _cr = db.exec_driver_sql(
                    "SELECT budget_usd, spent_usd FROM self_improve_cycles WHERE id = ?", (cycle_id,)
                ).fetchone()
            g2_result = verification_service.run_gate_with_retry(
                gate_name="G2_plan",
                input_data={"improvements": [dict(r._mapping) for r in approved]},
                output_data={
                    "steps": ordered,
                    "files": [f for item in ordered for f in item.get("estimated_files", [])],
                    "success_criteria": [],
                    "risks": [],
                },
                entity_type="cycle",
                entity_id=cycle_id,
                max_retries=2,
                budget_usd=_cr._mapping["budget_usd"] if _cr else None,
                spent_usd=_cr._mapping["spent_usd"] if _cr else 0.0,
            )
            if g2_result.verdict.value == "fail":
                log.warning("gate_failed", gate="G2", cycle_id=cycle_id, retries=g2_result.retry_count)
        except Exception as e:
            log.debug("g2_gate_skipped", error=str(e))

        # Spawn a Dev agent per improvement in its own worktree
        denylist_str = ", ".join(DENYLIST_PATTERNS)
        for imp_row in approved:
            # Budget check before each improvement
            if not self._check_budget(cycle_id):
                log.warning("budget_exceeded_during_dev", cycle_id=cycle_id)
                self._fail_cycle(cycle_id, "Budget exceeded during development")
                return

            # Disk space check before worktree creation
            if not _check_disk_space():
                log.warning("disk_space_low_during_dev", cycle_id=cycle_id)
                self._fail_cycle(cycle_id, f"Insufficient disk space (need at least {MIN_DISK_MB}MB free)")
                return

            imp_id = imp_row._mapping["id"]
            title = imp_row._mapping["title"]
            description = imp_row._mapping["description"]
            branch_name = f"self-improve/{cycle_id[:8]}/{imp_id[:8]}"

            try:
                wt = self.worktree_mgr.create(branch_name)
            except Exception as e:
                log.error("worktree_create_failed", improvement_id=imp_id, error=str(e))
                with get_db() as db:
                    db.exec_driver_sql(
                        "UPDATE self_improve_improvements SET status = 'failed', updated_at = ? WHERE id = ?",
                        (datetime.now(timezone.utc).isoformat(), imp_id),
                    )
                    pass  # auto-commit
                continue

            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE self_improve_improvements SET status = 'in_progress', "
                    "worktree_path = ?, branch_name = ?, updated_at = ? WHERE id = ?",
                    (str(wt.path), branch_name, datetime.now(timezone.utc).isoformat(), imp_id),
                )
                pass  # auto-commit

            prompt = SQUAD_ROLES["developer"]["prompt_template"].format(
                worktree_path=wt.path,
                branch_name=branch_name,
                title=title,
                description=description,
                denylist=denylist_str,
            )
            self._spawn_squad_agent(cycle_id, "developer", prompt, improvement_id=imp_id, worktree_path=str(wt.path))

        event_bus.emit("self_improve.stage_changed", {
            "cycle_id": cycle_id, "stage": "developing",
            "improvements_count": len(approved),
        })

    def _handle_dev_completed(self, cycle_id: str, improvement_id: str, output: str):
        """Dev completed — spawn Tester + Security for that worktree."""
        if not improvement_id:
            return

        imp = self.get_improvement(improvement_id)
        if not imp:
            return

        branch = imp["branch_name"]
        worktree_path = imp["worktree_path"]
        now = datetime.now(timezone.utc).isoformat()

        # Check denylist first
        violations = self.worktree_mgr.check_denylist(branch)
        if violations:
            log.error("denylist_violation", improvement_id=improvement_id, violations=violations)
            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE self_improve_improvements SET status = 'failed', "
                    "reject_reason = ?, updated_at = ? WHERE id = ?",
                    (f"Denylist violations: {'; '.join(violations)}", now, improvement_id),
                )
                pass  # auto-commit
            # Cleanup worktree
            try:
                self.worktree_mgr.cleanup(branch)
            except Exception as e:
                log.warning("cleanup_denylist_violation_failed", error=str(e))
            self._check_developing_complete(cycle_id)
            return

        # Update status
        with get_db() as db:
            diff_stat = self.worktree_mgr.get_diff_stat(branch)
            db.exec_driver_sql(
                "UPDATE self_improve_improvements SET status = 'testing', diff_stat = ?, updated_at = ? WHERE id = ?",
                (diff_stat, now, improvement_id),
            )
            db.commit()

        # Spawn Tester
        tester_prompt = SQUAD_ROLES["tester"]["prompt_template"].format(
            worktree_path=worktree_path,
            branch_name=branch,
        )
        self._spawn_squad_agent(cycle_id, "tester", tester_prompt, improvement_id=improvement_id, worktree_path=worktree_path)

        # Spawn Security
        denylist_str = ", ".join(DENYLIST_PATTERNS)
        security_prompt = SQUAD_ROLES["security"]["prompt_template"].format(
            branch_name=branch,
            repo_root=REPO_ROOT,
            denylist=denylist_str,
        )
        self._spawn_squad_agent(cycle_id, "security", security_prompt, improvement_id=improvement_id)

    def _handle_tester_completed(self, cycle_id: str, improvement_id: str, output: str):
        """Tester completed — store results, check if security also done."""
        if not improvement_id:
            return

        test_results = self._parse_json_from_output(output)
        if not isinstance(test_results, dict):
            test_results = {"passed": 0, "failed": 0, "errors": 1, "output": output[:2000]}

        now = datetime.now(timezone.utc).isoformat()
        with get_db() as db:
            db.exec_driver_sql(
                "UPDATE self_improve_improvements SET test_results = ?, updated_at = ? WHERE id = ?",
                (json.dumps(test_results), now, improvement_id),
            )
            db.commit()

        self._check_testing_complete_for_improvement(cycle_id, improvement_id)

    def _handle_security_completed(self, cycle_id: str, improvement_id: str, output: str):
        """Security completed — store results, check if tester also done."""
        if not improvement_id:
            return

        security_scan = self._parse_json_from_output(output)
        if not isinstance(security_scan, dict):
            security_scan = {"passed": False, "issues": ["Failed to parse security scan output"]}

        now = datetime.now(timezone.utc).isoformat()
        with get_db() as db:
            db.exec_driver_sql(
                "UPDATE self_improve_improvements SET security_scan = ?, updated_at = ? WHERE id = ?",
                (json.dumps(security_scan), now, improvement_id),
            )
            db.commit()

        self._check_testing_complete_for_improvement(cycle_id, improvement_id)

    def _check_testing_complete_for_improvement(self, cycle_id: str, improvement_id: str):
        """Check if both tester and security are done for an improvement."""
        imp = self.get_improvement(improvement_id)
        if not imp:
            return

        # Both must have results
        if imp["test_results"] is None or imp["security_scan"] is None:
            return  # Still waiting for the other agent

        now = datetime.now(timezone.utc).isoformat()
        test_results = imp["test_results"]
        security_scan = imp["security_scan"]

        # Check for failures
        tests_passed = test_results.get("failed", 0) == 0 and test_results.get("errors", 0) == 0
        security_passed = security_scan.get("passed", False)

        if not tests_passed or not security_passed:
            reasons = []
            if not tests_passed:
                reasons.append(f"Tests: {test_results.get('failed', 0)} failed, {test_results.get('errors', 0)} errors")
            if not security_passed:
                reasons.append(f"Security: {', '.join(security_scan.get('issues', []))}")

            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE self_improve_improvements SET status = 'failed', "
                    "reject_reason = ?, updated_at = ? WHERE id = ?",
                    ("; ".join(reasons), now, improvement_id),
                )
                pass  # auto-commit

            # Cleanup worktree
            if imp["branch_name"]:
                try:
                    self.worktree_mgr.cleanup(imp["branch_name"])
                except Exception as e:
                    log.warning("cleanup_failed_test", error=str(e))

            self._check_developing_complete(cycle_id)
            return

        # Run G3 implementation gate with retry before proceeding to review
        try:
            diff_for_gate = self.worktree_mgr.get_diff(imp["branch_name"]) if imp["branch_name"] else ""
            with get_db() as db:
                _cr = db.exec_driver_sql(
                    "SELECT budget_usd, spent_usd FROM self_improve_cycles WHERE id = ?", (cycle_id,)
                ).fetchone()
            g3_result = verification_service.run_gate_with_retry(
                gate_name="G3_implementation",
                input_data={"title": imp.get("title", ""), "description": imp.get("description", "")},
                output_data={
                    "diff": diff_for_gate[:5000] if diff_for_gate else "",
                    "test_results": test_results,
                    "security_scan": security_scan,
                    "changed_files": [],
                },
                entity_type="improvement",
                entity_id=improvement_id,
                max_retries=2,
                budget_usd=_cr._mapping["budget_usd"] if _cr else None,
                spent_usd=_cr._mapping["spent_usd"] if _cr else 0.0,
            )
            if g3_result.verdict.value == "fail":
                log.warning("gate_failed", gate="G3", improvement_id=improvement_id, retries=g3_result.retry_count)
        except Exception as e:
            log.debug("g3_gate_skipped", error=str(e))

        # Both passed — spawn Reviewer
        with get_db() as db:
            db.exec_driver_sql(
                "UPDATE self_improve_improvements SET status = 'review', updated_at = ? WHERE id = ?",
                (now, improvement_id),
            )
            db.commit()

        diff = self.worktree_mgr.get_diff(imp["branch_name"])
        # Truncate diff if too large for prompt
        if len(diff) > 15000:
            diff = diff[:15000] + "\n... (truncated)"

        reviewer_prompt = SQUAD_ROLES["reviewer"]["prompt_template"].format(diff=diff)
        self._spawn_squad_agent(cycle_id, "reviewer", reviewer_prompt, improvement_id=improvement_id)

        # Update cycle status if first to reach review
        with get_db() as db:
            cycle = db.exec_driver_sql(
                "SELECT status FROM self_improve_cycles WHERE id = ?", (cycle_id,)
            ).fetchone()
            if cycle and cycle._mapping["status"] in ("developing", "testing"):
                db.exec_driver_sql(
                    "UPDATE self_improve_cycles SET status = 'reviewing' WHERE id = ?",
                    (cycle_id,),
                )
                pass  # auto-commit

    def _handle_reviewer_completed(self, cycle_id: str, improvement_id: str, output: str):
        """Reviewer completed — if approved, spawn Doc Writer."""
        if not improvement_id:
            return

        review = self._parse_json_from_output(output)
        if not isinstance(review, dict):
            review = {"approved": False, "issues": ["Failed to parse review output"], "suggestions": []}

        now = datetime.now(timezone.utc).isoformat()
        review_notes = json.dumps(review)

        if not review.get("approved", False):
            # Review failed
            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE self_improve_improvements SET status = 'failed', "
                    "review_notes = ?, reject_reason = ?, updated_at = ? WHERE id = ?",
                    (
                        review_notes,
                        f"Review issues: {', '.join(review.get('issues', []))}",
                        now, improvement_id,
                    ),
                )
                pass  # auto-commit

            imp = self.get_improvement(improvement_id)
            if imp and imp["branch_name"]:
                try:
                    self.worktree_mgr.cleanup(imp["branch_name"])
                except Exception as e:
                    log.warning("cleanup_failed_review", error=str(e))

            self._check_developing_complete(cycle_id)
            return

        # Approved — spawn Doc Writer
        with get_db() as db:
            db.exec_driver_sql(
                "UPDATE self_improve_improvements SET status = 'documenting', review_notes = ?, updated_at = ? WHERE id = ?",
                (review_notes, now, improvement_id),
            )
            db.commit()

        imp = self.get_improvement(improvement_id)
        if not imp:
            return

        doc_prompt = SQUAD_ROLES["doc-writer"]["prompt_template"].format(
            title=imp["title"],
            description=imp["description"],
            diff_stat=imp["diff_stat"] or "N/A",
            test_results=json.dumps(imp["test_results"]) if imp["test_results"] else "N/A",
            review_notes=review_notes,
        )
        self._spawn_squad_agent(cycle_id, "doc-writer", doc_prompt, improvement_id=improvement_id)

        # Update cycle status
        with get_db() as db:
            db.exec_driver_sql(
                "UPDATE self_improve_cycles SET status = 'documenting' WHERE id = ?",
                (cycle_id,),
            )
            db.commit()

    def _handle_doc_writer_completed(self, cycle_id: str, improvement_id: str, output: str):
        """Doc Writer completed — mark awaiting_approval."""
        if not improvement_id:
            return

        doc_data = self._parse_json_from_output(output)
        pr_description = ""
        changelog_entry = ""
        if isinstance(doc_data, dict):
            pr_description = doc_data.get("pr_description", "")
            changelog_entry = doc_data.get("changelog_entry", "")

        now = datetime.now(timezone.utc).isoformat()
        imp = self.get_improvement(improvement_id)
        if not imp:
            return

        # Store diff summary for the approval UI
        diff_summary = ""
        if imp["branch_name"]:
            diff_summary = self.worktree_mgr.get_diff(imp["branch_name"])
            if len(diff_summary) > 10000:
                diff_summary = diff_summary[:10000] + "\n... (truncated)"

        with get_db() as db:
            db.exec_driver_sql(
                "UPDATE self_improve_improvements SET status = 'awaiting_approval', "
                "pr_description = ?, diff_summary = ?, updated_at = ? WHERE id = ?",
                (pr_description, diff_summary, now, improvement_id),
            )
            db.commit()

        event_bus.emit("self_improve.improvement_ready", {
            "improvement_id": improvement_id,
            "cycle_id": cycle_id,
            "title": imp["title"],
            "pr_description": pr_description,
        })

        # Update cycle status
        with get_db() as db:
            # Check if all active improvements are in awaiting_approval or terminal
            all_imp = db.exec_driver_sql(
                "SELECT status FROM self_improve_improvements WHERE cycle_id = ?",
                (cycle_id,),
            ).fetchall()
            non_terminal = [r._mapping["status"] for r in all_imp if r._mapping["status"] not in
                           ("awaiting_approval", "approved_by_human", "rejected_by_human", "merged", "failed")]
            if not non_terminal:
                db.exec_driver_sql(
                    "UPDATE self_improve_cycles SET status = 'awaiting_approval' WHERE id = ?",
                    (cycle_id,),
                )
                pass  # auto-commit
                event_bus.emit("self_improve.stage_changed", {
                    "cycle_id": cycle_id, "stage": "awaiting_approval",
                })

    def _handle_qa_lead_completed(self, cycle_id: str, output: str):
        """QA Lead completed — mark cycle as completed or failed."""
        qa_results = self._parse_json_from_output(output)
        if not isinstance(qa_results, dict):
            qa_results = {"all_passed": False, "regressions": ["Failed to parse QA output"], "integration_issues": []}

        now = datetime.now(timezone.utc).isoformat()

        # Run G4 acceptance gate with retry on QA results
        try:
            with get_db() as db:
                _cr = db.exec_driver_sql(
                    "SELECT budget_usd, spent_usd FROM self_improve_cycles WHERE id = ?", (cycle_id,)
                ).fetchone()
            g4_result = verification_service.run_gate_with_retry(
                gate_name="G4_acceptance",
                input_data={"requirements": []},
                output_data={
                    "criteria_met": [qa_results.get("all_passed", False)],
                    "review_notes": json.dumps(qa_results),
                    "changelog_entry": "",
                    "pr_description": "",
                },
                entity_type="cycle",
                entity_id=cycle_id,
                max_retries=2,
                budget_usd=_cr._mapping["budget_usd"] if _cr else None,
                spent_usd=_cr._mapping["spent_usd"] if _cr else 0.0,
            )
            if g4_result.verdict.value == "fail":
                log.warning("gate_failed", gate="G4", cycle_id=cycle_id, retries=g4_result.retry_count)
        except Exception as e:
            log.debug("g4_gate_skipped", error=str(e))

        if qa_results.get("all_passed", False):
            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE self_improve_cycles SET status = 'completed', completed_at = ? WHERE id = ?",
                    (now, cycle_id),
                )
                pass  # auto-commit

            with self._lock:
                if self._active_cycle_id == cycle_id:
                    self._active_cycle_id = None

            _release_lock()
            event_bus.emit("self_improve.cycle_completed", {"cycle_id": cycle_id})
        else:
            issues = qa_results.get("regressions", []) + qa_results.get("integration_issues", [])
            error_msg = f"QA failed: {'; '.join(issues)}" if issues else "QA failed"
            self._fail_cycle(cycle_id, error_msg)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_developing_complete(self, cycle_id: str):
        """Check if all improvements are done developing/testing/reviewing."""
        with get_db() as db:
            active = db.exec_driver_sql(
                "SELECT COUNT(*) FROM self_improve_improvements WHERE cycle_id = ? AND status IN "
                "('approved', 'in_progress', 'testing', 'review', 'documenting')",
                (cycle_id,),
            ).fetchone()[0]

            if active == 0:
                # All improvements are in terminal states or awaiting_approval
                non_terminal = db.exec_driver_sql(
                    "SELECT COUNT(*) FROM self_improve_improvements WHERE cycle_id = ? AND status = 'awaiting_approval'",
                    (cycle_id,),
                ).fetchone()[0]
                if non_terminal > 0:
                    db.exec_driver_sql(
                        "UPDATE self_improve_cycles SET status = 'awaiting_approval' WHERE id = ?",
                        (cycle_id,),
                    )
                    pass  # auto-commit
                    event_bus.emit("self_improve.stage_changed", {
                        "cycle_id": cycle_id, "stage": "awaiting_approval",
                    })
                else:
                    # All failed or rejected — nothing to approve
                    self._check_all_improvements_resolved(cycle_id)

    def _check_all_improvements_resolved(self, cycle_id: str):
        """Check if all improvements are in terminal state. If so, advance cycle."""
        with get_db() as db:
            pending = db.exec_driver_sql(
                "SELECT COUNT(*) FROM self_improve_improvements WHERE cycle_id = ? AND status NOT IN "
                "('merged', 'failed', 'rejected_by_human', 'approved_by_human')",
                (cycle_id,),
            ).fetchone()[0]

            if pending > 0:
                return

            # Check if any were merged — if so, run QA Lead
            merged_count = db.exec_driver_sql(
                "SELECT COUNT(*) FROM self_improve_improvements WHERE cycle_id = ? AND status = 'merged'",
                (cycle_id,),
            ).fetchone()[0]

            if merged_count > 0:
                db.exec_driver_sql(
                    "UPDATE self_improve_cycles SET status = 'integrating' WHERE id = ?",
                    (cycle_id,),
                )
                pass  # auto-commit

                # Spawn QA Lead
                prompt = SQUAD_ROLES["qa-lead"]["prompt_template"].format(repo_root=REPO_ROOT)
                self._spawn_squad_agent(cycle_id, "qa-lead", prompt)

                event_bus.emit("self_improve.stage_changed", {
                    "cycle_id": cycle_id, "stage": "integrating",
                })
            else:
                # All rejected or failed — cycle is done with no merges
                now = datetime.now(timezone.utc).isoformat()
                db.exec_driver_sql(
                    "UPDATE self_improve_cycles SET status = 'rejected', completed_at = ? WHERE id = ?",
                    (now, cycle_id),
                )
                pass  # auto-commit

                with self._lock:
                    if self._active_cycle_id == cycle_id:
                        self._active_cycle_id = None

                _release_lock()
                event_bus.emit("self_improve.cycle_completed", {
                    "cycle_id": cycle_id, "status": "rejected",
                })

    def _handle_agent_failure(self, cycle_id: str, role: str, improvement_id: str | None, output: str):
        """Handle a squad agent failure."""
        now = datetime.now(timezone.utc).isoformat()

        if improvement_id:
            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE self_improve_improvements SET status = 'failed', "
                    "reject_reason = ?, updated_at = ? WHERE id = ?",
                    (f"{role} agent failed: {output[:500]}", now, improvement_id),
                )
                pass  # auto-commit

            # Cleanup worktree if it exists
            imp = self.get_improvement(improvement_id)
            if imp and imp["branch_name"]:
                try:
                    self.worktree_mgr.cleanup(imp["branch_name"])
                except Exception as e:
                    log.warning("cleanup_failed_agent", error=str(e))

            self._check_developing_complete(cycle_id)
        else:
            # PM or Architect failed — cycle-level failure
            if role in ("pm", "architect"):
                self._fail_cycle(cycle_id, f"{role} agent failed: {output[:500]}")
            elif role == "qa-lead":
                self._fail_cycle(cycle_id, f"QA Lead failed: {output[:500]}")

    def _fail_cycle(self, cycle_id: str, error: str):
        """Mark a cycle as failed and cleanup."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as db:
            db.exec_driver_sql(
                "UPDATE self_improve_cycles SET status = 'failed', error = ?, completed_at = ? WHERE id = ?",
                (error[:2000], now, cycle_id),
            )
            db.commit()

        with self._lock:
            if self._active_cycle_id == cycle_id:
                self._active_cycle_id = None

        _release_lock()
        event_bus.emit("self_improve.cycle_failed", {"cycle_id": cycle_id, "error": error})

    def _spawn_squad_agent(
        self,
        cycle_id: str,
        role: str,
        task: str,
        improvement_id: str | None = None,
        worktree_path: str | None = None,
    ) -> str:
        """Spawn a squad agent using process_manager."""
        role_def = SQUAD_ROLES.get(role, {})
        agent_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        model = role_def.get("model", "sonnet")
        agent_name = role_def.get("name", f"Self-Improve {role}")

        # Create agent record
        with get_db() as db:
            db.exec_driver_sql(
                "INSERT INTO agents (id, name, model, role, status, task_description, "
                "working_directory, started_at, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'running', ?, ?, ?, ?, ?)",
                (
                    agent_id, f"[SI] {agent_name}", model,
                    f"self-improve-{role}", task[:500],
                    worktree_path or str(REPO_ROOT),
                    now, now, now,
                ),
            )

            # Link to cycle. Both INSERTs share this single get_db()
            # transaction (conn.begin()): get_db commits on clean exit and
            # rolls back on exception, so the agents row and its
            # self_improve_agents link are written atomically — both or
            # neither. (Previously an explicit db.commit() here made the two
            # inserts non-atomic and could leave an orphan agents row with no
            # cycle link.)
            db.exec_driver_sql(
                "INSERT INTO self_improve_agents (id, cycle_id, improvement_id, agent_id, role, status, started_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'running', ?, ?)",
                (str(uuid.uuid4()), cycle_id, improvement_id, agent_id, role, now, now),
            )

        # Check budget before spawning
        if not self._check_budget(cycle_id):
            log.warning("budget_exceeded", cycle_id=cycle_id)
            self._fail_cycle(cycle_id, "Budget exceeded")
            return agent_id

        # Spawn the process
        try:
            cwd = worktree_path or str(REPO_ROOT)
            pid = process_manager.spawn(agent_id, task, cwd=cwd, model=model, role=f"self-improve-{role}")

            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE agents SET pid = ? WHERE id = ?",
                    (pid, agent_id),
                )
                pass  # auto-commit

            log.info("squad_agent_spawned", agent_id=agent_id, role=role, cycle_id=cycle_id, pid=pid)
        except Exception as e:
            log.error("squad_agent_spawn_failed", role=role, error=str(e))
            with get_db() as db:
                db.exec_driver_sql(
                    "UPDATE agents SET status = 'failed', stopped_at = ? WHERE id = ?",
                    (now, agent_id),
                )
                db.exec_driver_sql(
                    "UPDATE self_improve_agents SET status = 'failed', completed_at = ? WHERE agent_id = ?",
                    (now, agent_id),
                )
                pass  # auto-commit
            raise

        return agent_id

    def _check_budget(self, cycle_id: str) -> bool:
        """Check if budget is exceeded. Returns True if within budget."""
        with get_db() as db:
            cycle = db.exec_driver_sql(
                "SELECT budget_usd FROM self_improve_cycles WHERE id = ?",
                (cycle_id,),
            ).fetchone()
            if not cycle:
                return False

            # Sum costs from all agents in this cycle
            agent_ids_rows = db.exec_driver_sql(
                "SELECT agent_id FROM self_improve_agents WHERE cycle_id = ?",
                (cycle_id,),
            ).fetchall()
            agent_ids = [r._mapping["agent_id"] for r in agent_ids_rows]

            if not agent_ids:
                return True

            placeholders = ",".join("?" for _ in agent_ids)
            # NOTE: params MUST be a tuple. Passing the raw list makes
            # exec_driver_sql treat it as executemany (expecting a list of
            # tuples/dicts) and raise "List argument must consist only of
            # tuples or dictionaries" -- which broke the budget check on the
            # very first agent spawn.
            cost_row = db.exec_driver_sql(
                f"SELECT COALESCE(SUM(cost_usd), 0.0) as total FROM cost_ledger WHERE agent_id IN ({placeholders})",
                tuple(agent_ids),
            ).fetchone()
            total_spent = cost_row._mapping["total"] if cost_row else 0.0

            # Update spent_usd
            db.exec_driver_sql(
                "UPDATE self_improve_cycles SET spent_usd = ? WHERE id = ?",
                (total_spent, cycle_id),
            )
            db.commit()

            return total_spent < cycle._mapping["budget_usd"]

    def _parse_json_from_output(self, output: str) -> dict | list | None:
        """Extract JSON from agent output, handling stream-json wrapper."""
        # The output may contain multiple stream-json lines. Look for the last
        # JSON object or array in the output.
        # Try direct parse first
        output = output.strip()

        # Try to find JSON in stream-json format — look for result content
        # stream-json emits lines like {"type":"result","result":"..."}
        lines = output.split("\n")
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
                # If it's a stream-json result envelope, extract the result
                if isinstance(parsed, dict) and "result" in parsed:
                    inner = parsed["result"]
                    if isinstance(inner, str):
                        try:
                            return json.loads(inner)
                        except json.JSONDecodeError:
                            pass
                    elif isinstance(inner, (dict, list)):
                        return inner
                # Direct JSON array or object
                if isinstance(parsed, (dict, list)):
                    return parsed
            except json.JSONDecodeError:
                continue

        # Try to extract JSON from text (find first [ or { and match)
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start_idx = output.find(start_char)
            if start_idx == -1:
                continue
            # Find matching end
            depth = 0
            for i in range(start_idx, len(output)):
                if output[i] == start_char:
                    depth += 1
                elif output[i] == end_char:
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(output[start_idx:i + 1])
                        except json.JSONDecodeError:
                            break

        log.warning("json_parse_failed", output_preview=output[:200])
        return None

    def get_squad_template(self) -> list[dict]:
        """Return the squad role definitions for the UI."""
        return [
            {
                "role": role,
                "name": info["name"],
                "stage": info["stage"],
                "model": info["model"],
            }
            for role, info in SQUAD_ROLES.items()
        ]

    def get_cycle_agents(self, cycle_id: str) -> list[dict]:
        """List all agents spawned for a cycle."""
        with get_db() as db:
            rows = db.exec_driver_sql(
                "SELECT sa.id, sa.cycle_id, sa.improvement_id, sa.agent_id, sa.role, "
                "sa.status, sa.started_at, sa.completed_at, sa.output_summary, sa.created_at, "
                "a.name, a.pid, a.model "
                "FROM self_improve_agents sa "
                "LEFT JOIN agents a ON sa.agent_id = a.id "
                "WHERE sa.cycle_id = ? ORDER BY sa.created_at",
                (cycle_id,),
            ).fetchall()
            return [dict(r._mapping) for r in rows]


# Module-level singleton
self_improve_service = SelfImproveService()
