import json
import uuid
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import insert, select, delete

from app.db.session import get_db
from app.db.tables import comments
from app.models.comments import CreateCommentBody, PatchCommentBody

router = APIRouter(tags=["Comments"])


@router.get("/api/comments")
def list_comments(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
):
    """List comments for an entity, returned as a flat list sorted by created_at.
    Client-side threading uses parent_id to build the tree."""
    with get_db() as conn:
        rows = conn.execute(
            select(
                comments.c.id, comments.c.entity_type, comments.c.entity_id,
                comments.c.parent_id, comments.c.author, comments.c.body,
                comments.c.mentions, comments.c.created_at, comments.c.updated_at,
            )
            .where(comments.c.entity_type == entity_type, comments.c.entity_id == entity_id)
            .order_by(comments.c.created_at.asc())
        ).fetchall()
        return [dict(r._mapping) for r in rows]


@router.post("/api/comments", status_code=201)
def create_comment(body: CreateCommentBody):
    comment_id = str(uuid.uuid4())
    mentions_json = json.dumps(body.mentions)

    with get_db() as conn:
        if body.parent_id:
            parent = conn.execute(
                select(comments.c.id, comments.c.entity_type, comments.c.entity_id)
                .where(comments.c.id == body.parent_id)
            ).fetchone()
            if not parent:
                raise HTTPException(404, "Parent comment not found")
            pm = parent._mapping
            if pm["entity_type"] != body.entity_type or pm["entity_id"] != body.entity_id:
                raise HTTPException(400, "Parent comment belongs to a different entity")

        conn.execute(
            insert(comments).values(
                id=comment_id,
                entity_type=body.entity_type,
                entity_id=body.entity_id,
                parent_id=body.parent_id,
                author=body.author,
                body=body.body,
                mentions=mentions_json,
            )
        )
        row = conn.execute(
            select(
                comments.c.id, comments.c.entity_type, comments.c.entity_id,
                comments.c.parent_id, comments.c.author, comments.c.body,
                comments.c.mentions, comments.c.created_at, comments.c.updated_at,
            ).where(comments.c.id == comment_id)
        ).fetchone()
        return dict(row._mapping)


@router.patch("/api/comments/{comment_id}")
def update_comment(comment_id: str, body: PatchCommentBody):
    updates: dict[str, str] = {}
    if body.body is not None:
        updates["body"] = body.body
    if body.mentions is not None:
        updates["mentions"] = json.dumps(body.mentions)

    if not updates:
        raise HTTPException(400, "No valid fields to update")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [comment_id]

    with get_db() as conn:
        result = conn.exec_driver_sql(
            f"UPDATE comments SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            tuple(values),
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Comment not found")
        row = conn.execute(
            select(
                comments.c.id, comments.c.entity_type, comments.c.entity_id,
                comments.c.parent_id, comments.c.author, comments.c.body,
                comments.c.mentions, comments.c.created_at, comments.c.updated_at,
            ).where(comments.c.id == comment_id)
        ).fetchone()
        return dict(row._mapping)


@router.delete("/api/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: str):
    with get_db() as conn:
        conn.execute(delete(comments).where(comments.c.parent_id == comment_id))
        result = conn.execute(delete(comments).where(comments.c.id == comment_id))
        if result.rowcount == 0:
            raise HTTPException(404, "Comment not found")
    return None
