import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func, insert, update, text
from app.db.session import get_db
from app.db.tables import (
    hub_projects, hub_content, hub_project_content, project_overrides,
)
from app.models.projects import ProjectUpdate

router = APIRouter(tags=["Projects"])

@router.get("/api/projects")
def list_projects():
    try:
        with get_db() as conn:
            # Subquery for item_count per project
            item_count_sq = (
                select(func.count())
                .select_from(hub_content)
                .join(hub_project_content, hub_content.c.id == hub_project_content.c.content_id)
                .where(hub_project_content.c.project_id == hub_projects.c.id)
                .correlate(hub_projects)
                .scalar_subquery()
                .label("item_count")
            )
            stmt = (
                select(
                    hub_projects.c.id,
                    hub_projects.c.name,
                    hub_projects.c.jira_key,
                    hub_projects.c.confluence_space,
                    hub_projects.c.active,
                    item_count_sq,
                )
                .order_by(hub_projects.c.name)
            )
            rows = conn.execute(stmt).fetchall()
            return [dict(r._mapping) for r in rows]
    except Exception:
        return []

@router.get("/api/projects/{project_id}")
def get_project(project_id: str):
    with get_db() as conn:
        row = conn.execute(
            select(hub_projects).where(hub_projects.c.id == project_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Project not found")
        project = dict(row._mapping)

        # Get content counts by source
        stmt = (
            select(hub_content.c.source, func.count().label("count"))
            .join(hub_project_content, hub_content.c.id == hub_project_content.c.content_id)
            .where(hub_project_content.c.project_id == project_id)
            .group_by(hub_content.c.source)
        )
        counts = conn.execute(stmt).fetchall()
        project["content_counts"] = {r.source: r.count for r in counts}

        # Overlay any platform overrides
        try:
            override = conn.execute(
                select(project_overrides.c.name, project_overrides.c.description)
                .where(project_overrides.c.hub_project_id == project_id)
            ).fetchone()
            if override:
                if override.name:
                    project["name"] = override.name
                if override.description:
                    project["description"] = override.description
        except Exception:
            pass

        return project


@router.patch("/api/projects/{project_id}")
def update_project(project_id: str, body: ProjectUpdate):
    """Update project name/description via platform.db overlay (hub.db stays read-only)."""
    with get_db() as conn:
        # Verify project exists
        row = conn.execute(
            select(hub_projects.c.id).where(hub_projects.c.id == project_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Project not found")

        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if not updates:
            raise HTTPException(400, "No fields to update")

        existing = conn.execute(
            select(project_overrides.c.hub_project_id)
            .where(project_overrides.c.hub_project_id == project_id)
        ).fetchone()

        if existing:
            conn.execute(
                update(project_overrides)
                .where(project_overrides.c.hub_project_id == project_id)
                .values(**updates)
            )
        else:
            conn.execute(
                insert(project_overrides).values(
                    id=str(uuid.uuid4()),
                    hub_project_id=project_id,
                    name=updates.get("name"),
                    description=updates.get("description"),
                )
            )

    # Return full project with overlay
    return get_project(project_id)
