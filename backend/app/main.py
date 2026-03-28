from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException as _HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import structlog
import time

from app.db.init_db import init_platform_db
from app.services.process_manager import process_manager
from app.services.id_generator import resolve_display_id as _resolve_display_id
from app.routers import (
    health, projects, teams, brain, content, agents, tasks,
    costs, todos, drafts, sessions, activity, events,
    settings, chat, dashboard, goals, tree, home, collaboration,
    tts, comments, templates, jarvis, analysis, stt, triggers,
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("platform_starting")
    init_platform_db()
    log.info("platform_db_initialized")
    process_manager.reconcile_on_startup()
    log.info("orphan_reconciliation_done")
    yield
    log.info("platform_stopping")

openapi_tags = [
    {"name": "System", "description": "Health checks and system status"},
    {"name": "Home", "description": "Home dashboard and briefing"},
    {"name": "Dashboard", "description": "Aggregated dashboard data"},
    {"name": "Projects", "description": "Knowledge Hub project management"},
    {"name": "Teams", "description": "Team hierarchy and metadata"},
    {"name": "Tree", "description": "Portfolio tree structure (nodes)"},
    {"name": "Agents", "description": "AI agent lifecycle and management"},
    {"name": "Tasks", "description": "Task tracking and state machine"},
    {"name": "Todos", "description": "Todo items from Knowledge Hub"},
    {"name": "Goals", "description": "Goal tracking and OKRs"},
    {"name": "Drafts", "description": "Draft review and approval queue"},
    {"name": "Chat", "description": "Claude chat sessions and messages"},
    {"name": "Costs", "description": "Cost tracking, budgets, and ledger"},
    {"name": "Activity", "description": "Governance and activity log"},
    {"name": "Events", "description": "Real-time SSE event streams"},
    {"name": "Sessions", "description": "CoCo CLI session history"},
    {"name": "Content", "description": "Knowledge Hub content browsing"},
    {"name": "Brain", "description": "People graph, rules, and queue"},
    {"name": "Settings", "description": "Platform configuration"},
    {"name": "Collaboration", "description": "Project context, handoffs, and workflows"},
    {"name": "Voice", "description": "Text-to-speech synthesis"},
    {"name": "Jarvis", "description": "Voice command interpreter"},
    {"name": "Comments", "description": "Threaded comments on entities"},
    {"name": "Templates", "description": "Project export/import templates"},
    {"name": "Analysis", "description": "Folder analysis pipeline"},
    {"name": "Triggers", "description": "Cron, webhook, and file-watch triggers"},
    {"name": "Webhooks", "description": "Incoming webhook receiver"},
]

app = FastAPI(
    title="CoCo Platform",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Response time middleware
@app.middleware("http")
async def add_response_time(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    response.headers["X-Response-Time"] = f"{duration:.1f}ms"
    if duration > 200:
        log.warning("slow_request", path=str(request.url.path), duration_ms=round(duration))
    return response

# Register routers
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(teams.router)
app.include_router(brain.router)
app.include_router(content.router)
app.include_router(agents.router)
app.include_router(tasks.router)
app.include_router(costs.router)
app.include_router(todos.router)
app.include_router(drafts.router)
app.include_router(sessions.router)
app.include_router(activity.router)
app.include_router(events.router)
app.include_router(settings.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(goals.router)
app.include_router(tree.router)
app.include_router(home.router)
app.include_router(collaboration.router)
app.include_router(tts.router)
app.include_router(jarvis.router)
app.include_router(comments.router)
app.include_router(templates.router)
app.include_router(analysis.router)
app.include_router(stt.router)
app.include_router(triggers.router)
app.include_router(triggers.webhook_router)

# --- Cross-cutting resolve endpoint ---

@app.get("/api/resolve/{display_id}", tags=["Search"])
def resolve_display_id(display_id: str):
    """Resolve a human-readable display ID (e.g. CXR-47) to entity type + id."""
    result = _resolve_display_id(display_id)
    if not result:
        raise _HTTPException(404, f"No entity found for display ID '{display_id}'")
    return result

# Serve static frontend in production
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
