from fastapi import APIRouter, HTTPException
from app.db.connections import get_hub_db, get_platform_db

router = APIRouter(tags=["Teams"])


def _node_map() -> dict:
    """Return a dict mapping hub_project_id -> node row for all linked nodes."""
    with get_platform_db() as db:
        rows = db.execute("""
            SELECT n.id AS node_id, n.hub_project_id, n.label, n.parent_id,
                   n.node_type, n.path, n.depth, n.icon, n.color,
                   (SELECT COUNT(*) FROM nodes c WHERE c.parent_id = n.id) AS child_count
            FROM nodes n
            WHERE n.hub_project_id IS NOT NULL
        """).fetchall()
        return {r["hub_project_id"]: dict(r) for r in rows}


@router.get("/api/teams")
def list_teams():
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

        nodes = _node_map()
        teams = []
        for r in rows:
            team = dict(r)
            team["team_id"] = team.pop("id")
            team["team_name"] = team.pop("name")
            node = nodes.get(team["team_id"])
            team["node_id"] = node["node_id"] if node else None
            team["child_count"] = node["child_count"] if node else 0
            teams.append(team)
        return teams
    except Exception:
        return []


@router.get("/api/teams/{team_id}")
def get_team(team_id: str):
    with get_hub_db() as db:
        row = db.execute(
            "SELECT id, name, jira_key, confluence_space, active FROM projects WHERE id = ?",
            (team_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Team not found")

        team = dict(row)
        team["team_id"] = team.pop("id")
        team["team_name"] = team.pop("name")

        counts = db.execute("""
            SELECT c.source, COUNT(*) as count
            FROM content c
            JOIN project_content pc ON c.id = pc.content_id
            WHERE pc.project_id = ?
            GROUP BY c.source
        """, (team_id,)).fetchall()
        team["content_counts"] = {r["source"]: r["count"] for r in counts}

    # Enrich with node metadata from platform.db
    with get_platform_db() as pdb:
        node = pdb.execute("""
            SELECT n.id AS node_id, n.parent_id, n.label, n.node_type,
                   n.path, n.depth, n.icon, n.color,
                   (SELECT COUNT(*) FROM nodes c WHERE c.parent_id = n.id) AS child_count
            FROM nodes n
            WHERE n.hub_project_id = ?
        """, (team_id,)).fetchone()
        if node:
            team["node_id"] = node["node_id"]
            team["child_count"] = node["child_count"]
            team["node_path"] = node["path"]
            team["node_depth"] = node["depth"]
            team["node_icon"] = node["icon"]
            team["node_color"] = node["color"]
        else:
            team["node_id"] = None
            team["child_count"] = 0

    return team
