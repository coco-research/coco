import uuid
from fastapi import APIRouter, HTTPException, Query
from app.db.connections import get_platform_db
from app.models.comments import CreateCommentBody, PatchCommentBody

router = APIRouter(tags=["Comments"])


@router.get("/api/comments")
def list_comments(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
):
    """List comments for an entity, returned as a flat list sorted by created_at.
    Client-side threading uses parent_id to build the tree."""
    with get_platform_db() as db:
        rows = db.execute(
            "SELECT id, entity_type, entity_id, parent_id, author, body, mentions, "
            "created_at, updated_at FROM comments "
            "WHERE entity_type = ? AND entity_id = ? "
            "ORDER BY created_at ASC",
            (entity_type, entity_id),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/api/comments", status_code=201)
def create_comment(body: CreateCommentBody):
    import json

    comment_id = str(uuid.uuid4())
    mentions_json = json.dumps(body.mentions)

    with get_platform_db() as db:
        # If replying, verify parent exists and belongs to same entity
        if body.parent_id:
            parent = db.execute(
                "SELECT id, entity_type, entity_id FROM comments WHERE id = ?",
                (body.parent_id,),
            ).fetchone()
            if not parent:
                raise HTTPException(404, "Parent comment not found")
            if parent["entity_type"] != body.entity_type or parent["entity_id"] != body.entity_id:
                raise HTTPException(400, "Parent comment belongs to a different entity")

        db.execute(
            "INSERT INTO comments (id, entity_type, entity_id, parent_id, author, body, mentions) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (comment_id, body.entity_type, body.entity_id, body.parent_id, body.author, body.body, mentions_json),
        )
        db.commit()
        row = db.execute(
            "SELECT id, entity_type, entity_id, parent_id, author, body, mentions, "
            "created_at, updated_at FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
        return dict(row)


@router.patch("/api/comments/{comment_id}")
def update_comment(comment_id: str, body: PatchCommentBody):
    import json

    updates: dict[str, str] = {}
    if body.body is not None:
        updates["body"] = body.body
    if body.mentions is not None:
        updates["mentions"] = json.dumps(body.mentions)

    if not updates:
        raise HTTPException(400, "No valid fields to update")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [comment_id]

    with get_platform_db() as db:
        result = db.execute(
            f"UPDATE comments SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(404, "Comment not found")
        row = db.execute(
            "SELECT id, entity_type, entity_id, parent_id, author, body, mentions, "
            "created_at, updated_at FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
        return dict(row)


@router.delete("/api/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: str):
    with get_platform_db() as db:
        # Delete child replies first, then the comment itself
        db.execute("DELETE FROM comments WHERE parent_id = ?", (comment_id,))
        result = db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(404, "Comment not found")
    return None
