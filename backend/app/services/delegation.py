"""Inter-agent delegation service."""
import json
import uuid
from datetime import datetime, timezone
import structlog
from app.db.connections import get_platform_db

log = structlog.get_logger()


class DelegationService:
    def delegate_task(
        self, task_id: str, from_agent_id: str, to_agent_id: str, context: dict | None = None
    ) -> dict:
        """Delegate an existing task from one agent to another."""
        with get_platform_db() as db:
            task = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            db.execute(
                "UPDATE tasks SET delegated_by = ?, delegated_to = ?, agent_id = ?, "
                "context_json = ?, status = 'in_progress', updated_at = ? WHERE id = ?",
                (
                    from_agent_id,
                    to_agent_id,
                    to_agent_id,
                    json.dumps(context or {}),
                    datetime.now(timezone.utc).isoformat(),
                    task_id,
                ),
            )
            db.commit()

            log.info("task_delegated", task_id=task_id, from_agent=from_agent_id, to_agent=to_agent_id)
            return dict(db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone())

    def create_subtask(
        self,
        parent_task_id: str,
        title: str,
        agent_id: str,
        node_id: str | None = None,
        context: dict | None = None,
    ) -> dict:
        """Create a subtask delegated from a parent task."""
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with get_platform_db() as db:
            parent = db.execute("SELECT * FROM tasks WHERE id = ?", (parent_task_id,)).fetchone()
            if not parent:
                raise ValueError(f"Parent task {parent_task_id} not found")

            db.execute(
                "INSERT INTO tasks (id, title, agent_id, node_id, project_id, status, priority, "
                "parent_task_id, delegated_by, delegated_to, context_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    title,
                    agent_id,
                    node_id or parent["node_id"],
                    parent["project_id"],
                    parent["priority"],
                    parent_task_id,
                    parent["agent_id"],
                    agent_id,
                    json.dumps(context or {}),
                    now,
                    now,
                ),
            )
            db.commit()

            log.info("subtask_created", task_id=task_id, parent=parent_task_id, agent=agent_id)
            return dict(db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone())

    def get_agent_queue(self, agent_id: str) -> list[dict]:
        """Get all tasks assigned to or delegated to an agent."""
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT * FROM tasks WHERE (agent_id = ? OR delegated_to = ?) "
                "AND status NOT IN ('done', 'cancelled', 'archived') ORDER BY priority, created_at",
                (agent_id, agent_id),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_delegation_chain(self, task_id: str) -> dict:
        """Get the full delegation chain for a task (parent -> subtasks)."""
        with get_platform_db() as db:
            # Walk up the parent chain
            chain: list[dict] = []
            current_id: str | None = task_id
            while current_id:
                row = db.execute("SELECT * FROM tasks WHERE id = ?", (current_id,)).fetchone()
                if not row:
                    break
                chain.insert(0, dict(row))
                current_id = row["parent_task_id"]

            # Get immediate subtasks
            subtasks = db.execute(
                "SELECT * FROM tasks WHERE parent_task_id = ? ORDER BY created_at",
                (task_id,),
            ).fetchall()

            return {"chain": chain, "subtasks": [dict(r) for r in subtasks]}


delegation_service = DelegationService()
