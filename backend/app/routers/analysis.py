"""
Analysis pipeline endpoints -- orchestrate folder analysis across agent teams.

POST /api/tree/{node_id}/analyze-folder  -- start an analysis job
GET  /api/analysis-jobs/{job_id}         -- get job status + results
GET  /api/analysis-jobs?node_id=X        -- list jobs for a node
"""

from __future__ import annotations

import json
import os
import uuid

from fastapi import APIRouter, HTTPException

from app.db.connections import get_platform_db
from app.services.folder_scanner import (
    build_folder_summary,
    read_file_content,
    scan_folder,
)
from app.services.process_manager import process_manager
from app.services.collaboration_context import build_collaboration_prompt
from app.models.analysis import AnalyzeFolderBody

router = APIRouter(tags=["Analysis"])


# ---------------------------------------------------------------------------
# Role-based analysis prompts
# ---------------------------------------------------------------------------

ROLE_ANALYSIS_PROMPTS: dict[str, str] = {
    "product-manager": (
        "Review these documents and extract:\n"
        "1. Key decisions made or pending\n"
        "2. Action items with owners and deadlines\n"
        "3. Stakeholders mentioned and their concerns\n"
        "4. Risks and blockers identified\n"
        "5. Requirements and acceptance criteria\n"
        "Format your output as structured markdown with clear headers."
    ),
    "chief-of-staff": (
        "Review these documents and provide an executive summary:\n"
        "1. Overall project status and health\n"
        "2. Key decisions that need escalation\n"
        "3. Cross-cutting themes and dependencies\n"
        "4. Recommended delegation and next steps\n"
        "5. Timeline and milestone assessment\n"
        "Format your output as a concise executive briefing."
    ),
    "technical-architect": (
        "Analyze these documents for technical content:\n"
        "1. Technical requirements and constraints\n"
        "2. Architecture decisions (made or needed)\n"
        "3. Dependencies and integration points\n"
        "4. Implementation notes and technical debt\n"
        "5. Data models and API contracts mentioned\n"
        "Format your output as a technical analysis with clear sections."
    ),
    "developer": (
        "Analyze these documents from an implementation perspective:\n"
        "1. Implementation tasks and specifications\n"
        "2. Code patterns and conventions mentioned\n"
        "3. Bug reports and issues described\n"
        "4. Testing requirements\n"
        "5. Configuration and environment details\n"
        "Format your output as actionable development notes."
    ),
    "qa-reviewer": (
        "Review these documents for quality issues:\n"
        "1. Gaps and missing information\n"
        "2. Inconsistencies or conflicting statements\n"
        "3. Ambiguous requirements that need clarification\n"
        "4. Quality risks and areas needing more detail\n"
        "5. Test scenarios suggested by the content\n"
        "Format your output as a quality review report."
    ),
    "user-researcher": (
        "Analyze these documents for user-related insights:\n"
        "1. User needs and pain points mentioned\n"
        "2. Feedback themes and patterns\n"
        "3. User experience implications\n"
        "4. Personas or user segments referenced\n"
        "5. Recommendations for user research\n"
        "Format your output as a user insights report."
    ),
    "project-manager": (
        "Analyze these documents for project management data:\n"
        "1. Timeline and milestone information\n"
        "2. Resource allocation and capacity\n"
        "3. Risks and mitigation strategies\n"
        "4. Dependencies and blockers\n"
        "5. Status updates and progress tracking\n"
        "Format your output as a project status summary."
    ),
    "data-analyst": (
        "Analyze these documents for data and metrics:\n"
        "1. Quantitative data and metrics mentioned\n"
        "2. Trends and patterns in the data\n"
        "3. KPIs and success measures referenced\n"
        "4. Data quality issues or gaps\n"
        "5. Opportunities for further analysis\n"
        "Format your output as a data analysis summary."
    ),
    "communications-specialist": (
        "Analyze these documents for communication needs:\n"
        "1. Key messages and narratives\n"
        "2. Stakeholder communication requirements\n"
        "3. Announcements or updates needed\n"
        "4. Tone and formatting observations\n"
        "5. Draft communication recommendations\n"
        "Format your output as a communications brief."
    ),
    "scribe": (
        "Process these documents and extract:\n"
        "1. Meeting notes and decisions\n"
        "2. Action items with assignments\n"
        "3. Key discussion points\n"
        "4. Follow-up items\n"
        "5. Links to related documents or decisions\n"
        "Format your output as structured notes."
    ),
}

ANALYSIS_TYPE_PREFIXES: dict[str, str] = {
    "full": "Perform a comprehensive analysis of the following documents.",
    "summary": "Provide a concise summary of the following documents. Focus on the key points, be brief.",
    "extract-actions": (
        "Extract all action items, TODO items, decisions, and next steps from the following documents. "
        "Format each as: - [ ] ACTION: <description> (owner: <who>, deadline: <when>)"
    ),
    "custom": "",  # Will use custom_prompt
}


def _build_file_context(files: list[dict], folder_path: str, max_content_chars: int = 200_000) -> str:
    """Build a text block with file listing and contents for small files."""
    lines: list[str] = []
    total_chars = 0

    lines.append(f"=== FOLDER: {folder_path} ===")
    lines.append(f"Total files to analyze: {len(files)}")
    lines.append("")

    # File listing
    lines.append("FILE LIST:")
    for f in files:
        size_kb = f["size_bytes"] / 1024
        lines.append(f"  - {f['name']} ({size_kb:.0f} KB, modified {f['modified_at'][:10]})")
    lines.append("")

    # File contents
    lines.append("=== FILE CONTENTS ===")
    for f in files:
        if total_chars >= max_content_chars:
            lines.append(f"\n... Remaining {len(files)} files omitted due to size limit ...")
            break

        content = read_file_content(f["path"], max_chars=min(30_000, max_content_chars - total_chars))
        header = f"\n--- {os.path.relpath(f['path'], folder_path)} ---"
        lines.append(header)
        lines.append(content)
        total_chars += len(content) + len(header)

    return "\n".join(lines)


def _build_agent_task(
    role: str,
    analysis_type: str,
    custom_prompt: str | None,
    file_context: str,
    folder_summary: str,
) -> str:
    """Build the full task prompt for an agent based on its role and analysis type."""
    parts: list[str] = []

    # Analysis type prefix
    prefix = ANALYSIS_TYPE_PREFIXES.get(analysis_type, ANALYSIS_TYPE_PREFIXES["full"])
    if analysis_type == "custom" and custom_prompt:
        prefix = custom_prompt
    elif custom_prompt:
        prefix = prefix + "\n\nAdditional instructions: " + custom_prompt

    parts.append(prefix)

    # Role-specific prompt
    role_prompt = ROLE_ANALYSIS_PROMPTS.get(role)
    if role_prompt:
        parts.append("")
        parts.append(f"As a {role.replace('-', ' ').title()}, specifically:")
        parts.append(role_prompt)
    else:
        parts.append("")
        parts.append("Summarize and extract key insights from these documents.")

    # Folder summary
    parts.append("")
    parts.append(folder_summary)

    # File contents
    parts.append("")
    parts.append(file_context)

    return "\n".join(parts)


def _convert_patterns_to_extensions(patterns: list[str]) -> list[str]:
    """Convert glob patterns like '*.md' to extensions like '.md'."""
    exts: list[str] = []
    for p in patterns:
        p = p.strip()
        if p.startswith("*."):
            exts.append(p[1:])  # *.md -> .md
        elif p.startswith("."):
            exts.append(p)
        else:
            exts.append(f".{p}")
    return exts


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/api/tree/{node_id}/analyze-folder", status_code=201)
def analyze_folder(node_id: str, body: AnalyzeFolderBody):
    """Start a folder analysis job: scan folder, assign tasks to agents, spawn them."""

    with get_platform_db() as db:
        # 1. Validate node
        node = db.execute(
            "SELECT id, folder_path, label FROM nodes WHERE id = ?",
            (node_id,),
        ).fetchone()
        if not node:
            raise HTTPException(404, "Node not found")

        folder_path = body.folder_path or (node["folder_path"] if node else None)
        if not folder_path:
            raise HTTPException(400, "No folder_path specified and node has no folder_path set")

        folder_path = os.path.expanduser(folder_path)
        if not os.path.isdir(folder_path):
            raise HTTPException(400, f"Folder does not exist: {folder_path}")

        # Security: must be under home directory
        home = os.path.expanduser("~")
        if not os.path.realpath(folder_path).startswith(home):
            raise HTTPException(403, "Folder must be within home directory")

        # 2. Get agents for this node
        agents = db.execute(
            "SELECT id, name, role, model, status, system_prompt FROM agents WHERE node_id = ?",
            (node_id,),
        ).fetchall()
        agents = [dict(a) for a in agents]

        if not agents:
            raise HTTPException(400, "No agents assigned to this node. Recruit agents first.")

        # Filter to idle/completed/failed agents (not currently running)
        available = [a for a in agents if a["status"] in ("idle", "completed", "failed", "killed")]
        if not available:
            raise HTTPException(
                409,
                "All agents on this node are currently running. Wait for them to complete or kill them first."
            )

        # 3. Scan the folder
        extensions = None
        if body.file_patterns:
            extensions = _convert_patterns_to_extensions(body.file_patterns)

        files = scan_folder(folder_path, extensions=extensions, max_files=body.max_files)
        if not files:
            raise HTTPException(400, "No matching files found in the folder")

        # 4. Build context
        folder_summary = build_folder_summary(folder_path)
        file_context = _build_file_context(files, folder_path)

        # 5. Create analysis job
        job_id = str(uuid.uuid4())
        spawned_ids: list[str] = []

        # 6. Spawn each available agent with a role-tailored task
        for agent in available:
            task = _build_agent_task(
                role=agent["role"] or "custom",
                analysis_type=body.analysis_type,
                custom_prompt=body.custom_prompt,
                file_context=file_context,
                folder_summary=folder_summary,
            )

            # Inject collaboration context
            collab_ctx = build_collaboration_prompt(node_id, agent["role"] or "custom")
            if collab_ctx:
                task = collab_ctx + "\n\n---\n\n" + task

            model = agent.get("model", "sonnet")

            try:
                pid = process_manager.spawn(
                    agent["id"],
                    task,
                    cwd=folder_path,
                    model=model,
                    node_id=node_id,
                    role=agent["role"],
                )
                db.execute(
                    """UPDATE agents SET status = 'running', pid = ?, started_at = datetime('now'),
                       stopped_at = NULL, exit_code = NULL, last_heartbeat = datetime('now'),
                       task_description = ?, working_directory = ?,
                       updated_at = datetime('now') WHERE id = ?""",
                    (pid, task[:2000], folder_path, agent["id"]),
                )
                spawned_ids.append(agent["id"])
            except RuntimeError:
                # Max concurrent agents reached -- stop spawning more
                break

        if not spawned_ids:
            raise HTTPException(429, "Could not spawn any agents -- max concurrent limit reached")

        # 7. Create job record
        db.execute(
            """INSERT INTO analysis_jobs
               (id, node_id, folder_path, analysis_type, status, file_count, agent_ids)
               VALUES (?, ?, ?, ?, 'running', ?, ?)""",
            (
                job_id,
                node_id,
                folder_path,
                body.analysis_type,
                len(files),
                json.dumps(spawned_ids),
            ),
        )
        db.commit()

        return {
            "job_id": job_id,
            "node_id": node_id,
            "folder_path": folder_path,
            "analysis_type": body.analysis_type,
            "status": "running",
            "file_count": len(files),
            "agent_count": len(spawned_ids),
            "agent_ids": spawned_ids,
        }


@router.get("/api/analysis-jobs/{job_id}")
def get_analysis_job(job_id: str):
    """Get an analysis job with agent statuses and results."""
    with get_platform_db() as db:
        job = db.execute(
            "SELECT * FROM analysis_jobs WHERE id = ?", (job_id,)
        ).fetchone()
        if not job:
            raise HTTPException(404, "Analysis job not found")

        result = dict(job)
        agent_ids = json.loads(result.get("agent_ids", "[]"))

        # Fetch agent statuses and output
        agents_info: list[dict] = []
        all_completed = True
        any_running = False

        for aid in agent_ids:
            agent = db.execute(
                "SELECT id, name, role, status, exit_code, started_at, stopped_at FROM agents WHERE id = ?",
                (aid,),
            ).fetchone()
            if not agent:
                continue
            agent_dict = dict(agent)

            # Get output text if completed
            if agent_dict["status"] == "completed":
                output_rows = db.execute(
                    "SELECT chunk FROM agent_output WHERE agent_id = ? ORDER BY id DESC LIMIT 50",
                    (aid,),
                ).fetchall()
                agent_dict["output"] = "\n".join(r["chunk"] for r in reversed(output_rows))
            else:
                agent_dict["output"] = None

            if agent_dict["status"] in ("running", "paused"):
                all_completed = False
                any_running = True
            elif agent_dict["status"] in ("idle",):
                all_completed = False

            agents_info.append(agent_dict)

        result["agents"] = agents_info

        # Auto-update job status
        if all_completed and result["status"] == "running":
            # Build results summary
            summaries: list[str] = []
            for ai in agents_info:
                if ai.get("output"):
                    role_label = (ai.get("role") or "agent").replace("-", " ").title()
                    summaries.append(f"## {role_label} ({ai['name']})\n\n{ai['output']}")
            results_summary = "\n\n---\n\n".join(summaries) if summaries else "No output captured."

            db.execute(
                """UPDATE analysis_jobs
                   SET status = 'completed', results_summary = ?, completed_at = datetime('now')
                   WHERE id = ?""",
                (results_summary, job_id),
            )
            db.commit()
            result["status"] = "completed"
            result["results_summary"] = results_summary

        return result


@router.get("/api/analysis-jobs")
def list_analysis_jobs(node_id: str | None = None):
    """List analysis jobs, optionally filtered by node_id."""
    with get_platform_db() as db:
        if node_id:
            rows = db.execute(
                "SELECT * FROM analysis_jobs WHERE node_id = ? ORDER BY created_at DESC",
                (node_id,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM analysis_jobs ORDER BY created_at DESC LIMIT 50"
            ).fetchall()

        results = []
        for row in rows:
            d = dict(row)
            d["agent_ids"] = json.loads(d.get("agent_ids", "[]"))
            results.append(d)

        return results
