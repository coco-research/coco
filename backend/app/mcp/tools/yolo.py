"""coco_yolo_activate, coco_yolo_classify, coco_mode -- Autonomy controls."""

from app.mcp.server import mcp
from app.config import CONFIG_JSON_PATH
from app.services.json_store import read_json, write_json


@mcp.tool()
def coco_yolo_activate(
    profile: str = "full",
    duration_minutes: int | None = None,
    project: str | None = None,
) -> dict:
    """Activate YOLO mode -- full autonomy for CoCo agents.

    Args:
        profile: Autonomy profile ('full', 'code-only', 'comms-safe'). Default: 'full'.
        duration_minutes: Optional auto-expire duration in minutes.
        project: Optional project scope (only apply YOLO to this project).
    """
    config = read_json(CONFIG_JSON_PATH)
    config["autonomy_mode"] = "yolo"
    config.setdefault("yolo", {})
    config["yolo"]["profile"] = profile
    config["yolo"]["duration_minutes"] = duration_minutes
    config["yolo"]["project_scope"] = project

    write_json(CONFIG_JSON_PATH, config)

    return {
        "mode": "yolo",
        "profile": profile,
        "duration_minutes": duration_minutes,
        "project_scope": project,
        "message": f"YOLO mode activated (profile={profile})."
        + (f" Expires in {duration_minutes}m." if duration_minutes else "")
        + (f" Scoped to project: {project}." if project else ""),
    }


@mcp.tool()
def coco_yolo_classify(action: str, context: str) -> dict:
    """Classify an action as safe or escalate based on YOLO rules and config.

    Used by agents to check whether an action can be auto-executed or needs human approval.

    Args:
        action: The action description (e.g. 'send email to client', 'refactor utils.py').
        context: Additional context about the action (project, agent role, etc.).
    """
    config = read_json(CONFIG_JSON_PATH)
    mode = config.get("autonomy_mode", "normal")

    if mode != "yolo":
        return {
            "classification": "escalate",
            "reason": f"Autonomy mode is '{mode}', not 'yolo'. All actions require approval.",
            "mode": mode,
        }

    yolo_config = config.get("yolo", {})
    profile = yolo_config.get("profile", "full")

    # Profile-based classification
    action_lower = action.lower()

    # Actions that always escalate regardless of profile
    always_escalate = [
        "delete", "remove production", "deploy to prod", "payment",
        "billing", "credential", "secret", "password",
    ]
    for keyword in always_escalate:
        if keyword in action_lower:
            return {
                "classification": "escalate",
                "reason": f"Action contains safety keyword '{keyword}' -- always requires approval.",
                "profile": profile,
            }

    if profile == "full":
        return {
            "classification": "safe",
            "reason": "Full YOLO mode -- action approved.",
            "profile": profile,
        }
    elif profile == "code-only":
        code_keywords = ["code", "refactor", "test", "fix", "implement", "build", "commit", "pr"]
        is_code = any(kw in action_lower for kw in code_keywords)
        return {
            "classification": "safe" if is_code else "escalate",
            "reason": "Code action approved." if is_code else "Non-code action requires approval in code-only profile.",
            "profile": profile,
        }
    elif profile == "comms-safe":
        comms_keywords = ["email", "slack", "message", "notify", "send", "publish"]
        is_comms = any(kw in action_lower for kw in comms_keywords)
        return {
            "classification": "escalate" if is_comms else "safe",
            "reason": "Communications require approval in comms-safe profile." if is_comms else "Non-comms action approved.",
            "profile": profile,
        }

    return {
        "classification": "safe",
        "reason": f"Unknown profile '{profile}' -- defaulting to safe.",
        "profile": profile,
    }


@mcp.tool()
def coco_mode(mode: str) -> dict:
    """Set CoCo's autonomy mode.

    Args:
        mode: One of 'yolo' (full autonomy), 'careful' (ask before acting), 'normal' (balanced).
    """
    valid_modes = ("yolo", "careful", "normal")
    if mode not in valid_modes:
        return {"error": f"Invalid mode '{mode}'. Must be one of: {valid_modes}"}

    config = read_json(CONFIG_JSON_PATH)
    old_mode = config.get("autonomy_mode", "normal")
    config["autonomy_mode"] = mode
    write_json(CONFIG_JSON_PATH, config)

    return {
        "mode": mode,
        "previous_mode": old_mode,
        "message": f"Autonomy mode changed from '{old_mode}' to '{mode}'.",
    }
