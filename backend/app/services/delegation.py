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
        """Get the full delegation chain for a task (parent -> subtasks), enriched with agent names."""
        with get_platform_db() as db:
            # Build agent name lookup
            agent_rows = db.execute("SELECT id, name FROM agents").fetchall()
            agent_names: dict[str, str] = {r["id"]: r["name"] for r in agent_rows}

            def enrich(row: dict) -> dict:
                """Add agent_name, delegated_by_name, delegated_to_name to a task dict."""
                d = dict(row)
                d["agent_name"] = agent_names.get(d.get("agent_id") or "", None)
                d["delegated_by_name"] = agent_names.get(d.get("delegated_by") or "", None)
                d["delegated_to_name"] = agent_names.get(d.get("delegated_to") or "", None)
                return d

            # Walk up the parent chain
            chain: list[dict] = []
            current_id: str | None = task_id
            depth = 0
            while current_id:
                row = db.execute("SELECT * FROM tasks WHERE id = ?", (current_id,)).fetchone()
                if not row:
                    break
                node = enrich(row)
                node["task_id"] = node["id"]
                node["task_title"] = node["title"]
                node["depth"] = 0  # will be recalculated
                chain.insert(0, node)
                current_id = row["parent_task_id"]

            # Assign correct depths (root = 0)
            for i, node in enumerate(chain):
                node["depth"] = i

            # Get immediate subtasks
            subtasks = db.execute(
                "SELECT * FROM tasks WHERE parent_task_id = ? ORDER BY created_at",
                (task_id,),
            ).fetchall()

            enriched_subtasks = []
            for s in subtasks:
                node = enrich(s)
                node["task_id"] = node["id"]
                node["task_title"] = node["title"]
                node["depth"] = (chain[-1]["depth"] + 1) if chain else 1
                enriched_subtasks.append(node)

            # Return flat chain = ancestors + current + subtasks (for timeline rendering)
            full_chain = chain + enriched_subtasks
            return full_chain

    def get_node_task_board(self, node_id: str) -> list[dict]:
        """Get all tasks for agents in a node (subtree), enriched with agent names."""
        with get_platform_db() as db:
            # Get all agent IDs in this node subtree
            agent_rows = db.execute(
                "SELECT id, name FROM agents WHERE node_id = ?", (node_id,)
            ).fetchall()
            agent_names: dict[str, str] = {r["id"]: r["name"] for r in agent_rows}
            agent_ids = list(agent_names.keys())

            if not agent_ids:
                return []

            placeholders = ",".join("?" for _ in agent_ids)
            rows = db.execute(
                f"SELECT id, title, description, agent_id, node_id, project_id, status, priority, "
                f"delegated_by, delegated_to, parent_task_id, created_at, updated_at "
                f"FROM tasks WHERE agent_id IN ({placeholders}) OR delegated_to IN ({placeholders}) "
                f"ORDER BY created_at DESC",
                agent_ids + agent_ids,
            ).fetchall()

            # Also fetch names for agents that might be outside this node (delegated_by)
            all_agent_rows = db.execute("SELECT id, name FROM agents").fetchall()
            all_names: dict[str, str] = {r["id"]: r["name"] for r in all_agent_rows}

            result = []
            seen = set()
            for r in rows:
                if r["id"] in seen:
                    continue
                seen.add(r["id"])
                d = dict(r)
                d["agent_name"] = all_names.get(d.get("agent_id") or "", None)
                d["delegated_by_name"] = all_names.get(d.get("delegated_by") or "", None)
                result.append(d)

            return result

    def get_agent_delegations(self, agent_id: str) -> dict:
        """Get tasks delegated BY this agent and tasks delegated TO this agent."""
        with get_platform_db() as db:
            # Agent name lookup
            agent_rows = db.execute("SELECT id, name FROM agents").fetchall()
            agent_names: dict[str, str] = {r["id"]: r["name"] for r in agent_rows}

            def enrich(row) -> dict:
                d = dict(row)
                d["agent_name"] = agent_names.get(d.get("agent_id") or "", None)
                d["delegated_by_name"] = agent_names.get(d.get("delegated_by") or "", None)
                d["delegated_to_name"] = agent_names.get(d.get("delegated_to") or "", None)
                return d

            delegated_by = db.execute(
                "SELECT * FROM tasks WHERE delegated_by = ? AND status NOT IN ('archived') "
                "ORDER BY created_at DESC",
                (agent_id,),
            ).fetchall()

            delegated_to = db.execute(
                "SELECT * FROM tasks WHERE delegated_to = ? AND delegated_by != ? "
                "AND status NOT IN ('archived') ORDER BY created_at DESC",
                (agent_id, agent_id),
            ).fetchall()

            return {
                "delegated_by_me": [enrich(r) for r in delegated_by],
                "delegated_to_me": [enrich(r) for r in delegated_to],
            }


delegation_service = DelegationService()
