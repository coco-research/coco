"""coco_decide -- List queue items or take action on one."""

from app.mcp.server import mcp
from app.config import QUEUE_JSON_PATH
from app.services.json_store import read_json, write_json


def _get_queue_items() -> list[dict]:
    """Read and normalize queue items from queue.json."""
    data = read_json(QUEUE_JSON_PATH)
    if isinstance(data, dict):
        items = data.get("items", [])
    elif isinstance(data, list):
        items = data
    else:
        items = []

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "id": item.get("id", ""),
            "priority": item.get("priority", "medium"),
            "type": item.get("type", "unknown"),
            "summary": item.get("summary", ""),
            "project": item.get("project"),
            "source": item.get("source"),
            "created_at": item.get("created_at"),
            "status": item.get("status", "pending"),
        })
    return normalized


@mcp.tool()
def coco_decide(item_index: int | None = None, action: str | None = None) -> dict:
    """List decision queue items, or take action on a specific item.

    Without arguments: returns all pending queue items.
    With item_index + action: applies the action ('approve', 'reject', 'defer', 'dismiss') to the item at that index.

    Args:
        item_index: 0-based index of the queue item to act on.
        action: One of 'approve', 'reject', 'defer', 'dismiss'.
    """
    items = _get_queue_items()

    if item_index is None:
        return {"items": items, "total": len(items)}

    if item_index < 0 or item_index >= len(items):
        return {"error": f"Invalid index {item_index}. Queue has {len(items)} items (0-{len(items) - 1})."}

    valid_actions = ("approve", "reject", "defer", "dismiss")
    if action not in valid_actions:
        return {"error": f"Invalid action '{action}'. Must be one of: {valid_actions}"}

    # Apply action
    data = read_json(QUEUE_JSON_PATH)
    if isinstance(data, dict):
        raw_items = data.get("items", [])
    elif isinstance(data, list):
        raw_items = data
    else:
        return {"error": "Queue file is malformed."}

    if item_index >= len(raw_items):
        return {"error": f"Index {item_index} out of range."}

    target = raw_items[item_index]
    target["status"] = action + "d" if action != "dismiss" else "dismissed"

    if action == "defer":
        # Move to deferred list
        if isinstance(data, dict):
            data.setdefault("deferred", []).append(target)
            data["items"] = [i for idx, i in enumerate(raw_items) if idx != item_index]
        else:
            data = [i for idx, i in enumerate(raw_items) if idx != item_index]
    elif action == "dismiss":
        # Remove from items
        if isinstance(data, dict):
            data["items"] = [i for idx, i in enumerate(raw_items) if idx != item_index]
        else:
            data = [i for idx, i in enumerate(raw_items) if idx != item_index]
    else:
        # Update in place for approve/reject
        if isinstance(data, dict):
            data["items"] = raw_items
        else:
            data = raw_items

    write_json(QUEUE_JSON_PATH, data)

    return {
        "action": action,
        "item": target,
        "remaining": len(data.get("items", data) if isinstance(data, dict) else data),
    }
