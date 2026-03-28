"""coco_activate -- Returns full dashboard data."""

from app.mcp.server import mcp
from app.routers.home import get_home


@mcp.tool()
def coco_activate() -> dict:
    """Activate CoCo and get the full dashboard: greeting, projects, todos, attention items, health status, queue items, costs, and session info.

    Call this at the start of a session to get a complete picture of current state.
    """
    return get_home()
