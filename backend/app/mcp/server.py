"""CoCo Platform MCP Server -- 22 tools wrapping the Platform backend."""
import sys
from pathlib import Path

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "coco-platform",
    instructions="CoCo Platform -- PM-centric AI agent control plane",
)

# Import all tool modules (registration happens at import time via @mcp.tool())
from app.mcp.tools import activate, decide, brain, yolo, todos, system, session  # noqa: F401, E402

if __name__ == "__main__":
    mcp.run()
