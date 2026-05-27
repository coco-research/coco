"""Git worktree manager for self-improve feature.

Manages isolated git worktrees so self-improve agents never touch the main branch directly.
"""

import fnmatch
import re
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path

import structlog

log = structlog.get_logger()

REPO_ROOT = Path(__file__).parent.parent.parent.parent  # coco-platform root
WORKTREE_BASE = REPO_ROOT / ".worktrees"

DENYLIST_PATTERNS = [
    "*.db",
    ".env",
    ".env.*",
    "credentials*",
    "backend/app/services/self_improve.py",
    "backend/app/services/worktree_manager.py",
    "backend/app/routers/self_improve.py",
    "backend/app/models/self_improve.py",
    "frontend/src/pages/SelfImprovePage.tsx",
    "frontend/src/components/self-improve/*",
]


@dataclass
class WorktreeInfo:
    path: Path
    branch: str
    created: bool


class WorktreeManager:
    def __init__(self, repo_root: Path = REPO_ROOT):
        self.repo_root = repo_root
        self.worktree_base = repo_root / ".worktrees"

    def _run_git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        """Run a git command from the repo root. Raises on failure."""
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=cwd or self.repo_root,
        )
        return result

    def create(self, branch_name: str) -> WorktreeInfo:
        """Create a new git worktree with an isolated branch."""
        self.worktree_base.mkdir(parents=True, exist_ok=True)
        worktree_path = self.worktree_base / branch_name

        if worktree_path.exists():
            log.warning("worktree_already_exists", branch=branch_name, path=str(worktree_path))
            return WorktreeInfo(path=worktree_path, branch=branch_name, created=False)

        result = self._run_git(
            "worktree", "add", "-b", branch_name,
            str(worktree_path), "main",
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to create worktree '{branch_name}': {result.stderr.strip()}"
            )

        log.info("worktree_created", branch=branch_name, path=str(worktree_path))
        return WorktreeInfo(path=worktree_path, branch=branch_name, created=True)

    def get_diff(self, branch_name: str) -> str:
        """Get the full diff of changes in a worktree."""
        result = self._run_git("diff", f"main...{branch_name}")
        if result.returncode != 0:
            log.warning("git_diff_failed", branch=branch_name, stderr=result.stderr.strip())
            return ""
        return result.stdout

    def get_diff_stat(self, branch_name: str) -> str:
        """Get diff stat (files changed, insertions, deletions)."""
        result = self._run_git("diff", "--stat", f"main...{branch_name}")
        if result.returncode != 0:
            log.warning("git_diff_stat_failed", branch=branch_name, stderr=result.stderr.strip())
            return ""
        return result.stdout.strip()

    def get_changed_files(self, branch_name: str) -> list[str]:
        """List files changed in the worktree branch."""
        result = self._run_git("diff", "--name-only", f"main...{branch_name}")
        if result.returncode != 0:
            log.warning("git_changed_files_failed", branch=branch_name, stderr=result.stderr.strip())
            return []
        return [f for f in result.stdout.strip().split("\n") if f]

    def check_denylist(self, branch_name: str) -> list[str]:
        """Check if any changed files match the denylist. Returns list of violations."""
        changed = self.get_changed_files(branch_name)
        violations: list[str] = []
        for filepath in changed:
            for pattern in DENYLIST_PATTERNS:
                if fnmatch.fnmatch(filepath, pattern):
                    violations.append(f"{filepath} matches denylist pattern '{pattern}'")
                    break
        return violations

    def run_tests(self, worktree_path: Path) -> dict:
        """Run pytest + linting in the worktree. Returns {passed, failed, errors, output}."""
        results = {"passed": 0, "failed": 0, "errors": 0, "output": ""}
        output_parts: list[str] = []

        # Run pytest
        pytest_result = subprocess.run(
            ["python", "-m", "pytest", "backend/", "--tb=short", "-q"],
            capture_output=True,
            text=True,
            cwd=worktree_path,
            timeout=300,
        )
        output_parts.append("=== pytest ===\n" + pytest_result.stdout)
        if pytest_result.stderr:
            output_parts.append(pytest_result.stderr)

        # Parse pytest output for counts
        for line in pytest_result.stdout.split("\n"):
            line = line.strip()
            # e.g. "5 passed, 2 failed, 1 error in 3.21s"
            if "passed" in line or "failed" in line or "error" in line:
                passed_match = re.search(r"(\d+) passed", line)
                failed_match = re.search(r"(\d+) failed", line)
                errors_match = re.search(r"(\d+) error", line)
                if passed_match:
                    results["passed"] = int(passed_match.group(1))
                if failed_match:
                    results["failed"] = int(failed_match.group(1))
                if errors_match:
                    results["errors"] = int(errors_match.group(1))

        # Run ruff linting
        ruff_result = subprocess.run(
            ["ruff", "check", "backend/"],
            capture_output=True,
            text=True,
            cwd=worktree_path,
            timeout=60,
        )
        output_parts.append("\n=== ruff check ===\n" + ruff_result.stdout)
        if ruff_result.stderr:
            output_parts.append(ruff_result.stderr)
        if ruff_result.returncode != 0:
            results["errors"] += 1

        results["output"] = "\n".join(output_parts)
        return results

    def merge(self, branch_name: str) -> bool:
        """Merge worktree branch into main. Returns True on success."""
        # First checkout main
        result = self._run_git("checkout", "main")
        if result.returncode != 0:
            log.error("git_checkout_main_failed", stderr=result.stderr.strip())
            return False

        # Merge with no-ff
        result = self._run_git("merge", "--no-ff", branch_name, "-m",
                               f"self-improve: merge {branch_name}")
        if result.returncode != 0:
            log.error("git_merge_failed", branch=branch_name, stderr=result.stderr.strip())
            # Abort the merge if it failed
            self._run_git("merge", "--abort")
            return False

        log.info("worktree_merged", branch=branch_name)
        return True

    def cleanup(self, branch_name: str) -> None:
        """Remove worktree and delete branch."""
        worktree_path = self.worktree_base / branch_name

        # Remove the worktree
        result = self._run_git("worktree", "remove", str(worktree_path), "--force")
        if result.returncode != 0:
            log.warning("worktree_remove_failed", branch=branch_name, stderr=result.stderr.strip())
            # Fallback: remove directory manually
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
            # Prune worktree references
            self._run_git("worktree", "prune")

        # Delete the branch
        result = self._run_git("branch", "-D", branch_name)
        if result.returncode != 0:
            log.warning("branch_delete_failed", branch=branch_name, stderr=result.stderr.strip())

        log.info("worktree_cleaned_up", branch=branch_name)

    def cleanup_all(self) -> None:
        """Remove all self-improve worktrees."""
        if not self.worktree_base.exists():
            return

        # List all worktrees
        result = self._run_git("worktree", "list", "--porcelain")
        if result.returncode != 0:
            log.warning("worktree_list_failed", stderr=result.stderr.strip())
            return

        # Find worktrees under our base directory
        branches_to_clean: list[str] = []
        current_worktree: str | None = None
        current_branch: str | None = None

        for line in result.stdout.split("\n"):
            if line.startswith("worktree "):
                current_worktree = line.split(" ", 1)[1]
            elif line.startswith("branch "):
                ref = line.split(" ", 1)[1]
                current_branch = ref.replace("refs/heads/", "")
            elif line == "" and current_worktree and current_branch:
                if str(self.worktree_base) in current_worktree:
                    branches_to_clean.append(current_branch)
                current_worktree = None
                current_branch = None

        for branch in branches_to_clean:
            try:
                self.cleanup(branch)
            except Exception as e:
                log.warning("cleanup_single_failed", branch=branch, error=str(e))

        # Final prune
        self._run_git("worktree", "prune")
        log.info("all_worktrees_cleaned", count=len(branches_to_clean))
