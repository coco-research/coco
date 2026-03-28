from fastapi import APIRouter, HTTPException
from app.db.connections import get_hub_db, get_platform_db
from app.models.projects import ProjectUpdate

router = APIRouter(tags=["Projects"])

@router.get("/api/projects")
def list_projects():
    try:
        with get_hub_db() as db:
            rows = db.execute("""
                SELECT p.id, p.name, p.jira_key, p.confluence_space, p.active,
                    (SELECT COUNT(*) FROM content c
                     JOIN project_content pc ON c.id = pc.content_id
                     WHERE pc.project_id = p.id) as item_count
                FROM projects p
                ORDER BY p.name
            """).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        return []

@router.get("/api/projects/{project_id}")
def get_project(project_id: str):
    with get_hub_db() as db:
        row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Project not found")
        project = dict(row)
        # Get content counts by source
        counts = db.execute("""
            SELECT c.source, COUNT(*) as count
            FROM content c
            JOIN project_content pc ON c.id = pc.content_id
            WHERE pc.project_id = ?
            GROUP BY c.source
        """, (project_id,)).fetchall()
        project["content_counts"] = {r["source"]: r["count"] for r in counts}

        # Overlay any platform.db overrides
        try:
            with get_platform_db() as pdb:
                override = pdb.execute(
                    "SELECT name, description FROM project_overrides WHERE hub_project_id = ?",
                    (project_id,),
                ).fetchone()
                if override:
                    if override["name"]:
                        project["name"] = override["name"]
                    if override["description"]:
                        project["description"] = override["description"]
        except Exception:
            pass

        return project


@router.patch("/api/projects/{project_id}")
def update_project(project_id: str, body: ProjectUpdate):
    """Update project name/description via platform.db overlay (hub.db stays read-only)."""
    # Verify project exists in hub.db
    with get_hub_db() as db:
        row = db.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Project not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")

    with get_platform_db() as pdb:
        existing = pdb.execute(
            "SELECT hub_project_id FROM project_overrides WHERE hub_project_id = ?",
            (project_id,),
        ).fetchone()

        if existing:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [project_id]
            pdb.execute(
                f"UPDATE project_overrides SET {set_clause} WHERE hub_project_id = ?",
                values,
            )
        else:
            import uuid
            pdb.execute(
                "INSERT INTO project_overrides (id, hub_project_id, name, description) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), project_id, updates.get("name"), updates.get("description")),
            )
        pdb.commit()

    # Return full project with overlay
    return get_project(project_id)
