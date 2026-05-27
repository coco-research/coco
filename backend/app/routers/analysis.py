"""
Analysis pipeline endpoints -- orchestrate folder analysis across agent teams.

POST /api/tree/{node_id}/analyze-folder  -- start an analysis job
GET  /api/analysis-jobs/{job_id}         -- get job status + results
GET  /api/analysis-jobs?node_id=X        -- list jobs for a node
"""

from __future__ import annotations

import json
import os
import re
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import insert, select, update

from app.db.session import get_db
from app.db.compat import now
from app.db.tables import agents, agent_output, analysis_jobs, nodes, hub_todos
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
# Helpers
# ---------------------------------------------------------------------------

def _clean_agent_output(raw: str) -> str:
    """Strip stream-json system/hook lines from stored agent output.

    Old output stored before the parser was added contains raw JSON events.
    This retroactively extracts only human-readable text.
    """
    lines = raw.split("\n")
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue
        # Try to detect raw stream-json lines
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                obj = json.loads(stripped)
                etype = obj.get("type", "")
                # Extract text from content_block_delta
                if etype == "content_block_delta":
                    delta = obj.get("delta", {})
                    if delta.get("type") == "text_delta":
                        t = delta.get("text", "")
                        if t:
                            cleaned.append(t)
                    continue
                # Extract from result event
                if etype == "result":
                    t = obj.get("result", "")
                    if t:
                        cleaned.append(t)
                    continue
                # Extract from assistant message
                if etype == "assistant":
                    for block in obj.get("content", []):
                        if isinstance(block, dict) and block.get("type") == "text":
                            cleaned.append(block.get("text", ""))
                    continue
                # Skip system, hook_started, hook_response, etc.
                if etype in ("system", "tool_use", "tool_result", ""):
                    continue
                # Unknown JSON — skip
                continue
            except (ValueError, TypeError):
                pass
        # Not JSON — keep as-is (actual text content)
        cleaned.append(line)
    result = "\n".join(cleaned).strip()
    return result if result else "No output captured."


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

    prefix = ANALYSIS_TYPE_PREFIXES.get(analysis_type, ANALYSIS_TYPE_PREFIXES["full"])
    if analysis_type == "custom" and custom_prompt:
        prefix = custom_prompt
    elif custom_prompt:
        prefix = prefix + "\n\nAdditional instructions: " + custom_prompt

    parts.append(prefix)

    role_prompt = ROLE_ANALYSIS_PROMPTS.get(role)
    if role_prompt:
        parts.append("")
        parts.append(f"As a {role.replace('-', ' ').title()}, specifically:")
        parts.append(role_prompt)
    else:
        parts.append("")
        parts.append("Summarize and extract key insights from these documents.")

    parts.append("")
    parts.append(folder_summary)
    parts.append("")
    parts.append(file_context)

    return "\n".join(parts)


def _convert_patterns_to_extensions(patterns: list[str]) -> list[str]:
    """Convert glob patterns like '*.md' to extensions like '.md'."""
    exts: list[str] = []
    for p in patterns:
        p = p.strip()
        if p.startswith("*."):
            exts.append(p[1:])
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

    with get_db() as conn:
        # 1. Validate node
        node = conn.execute(
            select(nodes.c.id, nodes.c.folder_path, nodes.c.label).where(nodes.c.id == node_id)
        ).fetchone()
        if not node:
            raise HTTPException(404, "Node not found")

        folder_path = body.folder_path or (node._mapping["folder_path"] if node else None)
        if not folder_path:
            raise HTTPException(400, "No folder_path specified and node has no folder_path set")

        folder_path = os.path.expanduser(folder_path)
        if not os.path.isdir(folder_path):
            raise HTTPException(400, f"Folder does not exist: {folder_path}")

        home = os.path.expanduser("~")
        if not os.path.realpath(folder_path).startswith(home):
            raise HTTPException(403, "Folder must be within home directory")

        # 2. Get agents for this node
        agent_rows = conn.execute(
            select(
                agents.c.id, agents.c.name, agents.c.role,
                agents.c.model, agents.c.status, agents.c.system_prompt,
            ).where(agents.c.node_id == node_id)
        ).fetchall()
        agents_list = [dict(a._mapping) for a in agent_rows]

        if not agents_list:
            raise HTTPException(400, "No agents assigned to this node. Recruit agents first.")

        available = [a for a in agents_list if a["status"] in ("idle", "completed", "failed", "killed")]
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
                conn.execute(
                    update(agents)
                    .where(agents.c.id == agent["id"])
                    .values(
                        status="running",
                        pid=pid,
                        started_at=now(),
                        stopped_at=None,
                        exit_code=None,
                        last_heartbeat=now(),
                        task_description=task[:2000],
                        working_directory=folder_path,
                        updated_at=now(),
                    )
                )
                spawned_ids.append(agent["id"])
            except RuntimeError:
                break

        if not spawned_ids:
            raise HTTPException(429, "Could not spawn any agents -- max concurrent limit reached")

        # 7. Create job record
        conn.execute(
            insert(analysis_jobs).values(
                id=job_id,
                node_id=node_id,
                folder_path=folder_path,
                analysis_type=body.analysis_type,
                status="running",
                file_count=len(files),
                agent_ids=json.dumps(spawned_ids),
            )
        )

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
    with get_db() as conn:
        job = conn.execute(
            select(analysis_jobs).where(analysis_jobs.c.id == job_id)
        ).fetchone()
        if not job:
            raise HTTPException(404, "Analysis job not found")

        result = dict(job._mapping)
        agent_ids = json.loads(result.get("agent_ids", "[]"))

        agents_info: list[dict] = []
        all_completed = True
        any_running = False

        for aid in agent_ids:
            agent = conn.exec_driver_sql(
                "SELECT id, name, role, status, exit_code, started_at, stopped_at FROM agents WHERE id = ?",
                (aid,),
            ).fetchone()
            if not agent:
                continue
            agent_dict = dict(agent._mapping)

            if agent_dict["status"] == "completed":
                output_rows = conn.exec_driver_sql(
                    "SELECT chunk FROM agent_output WHERE agent_id = ? ORDER BY id DESC LIMIT 200",
                    (aid,),
                ).fetchall()
                raw_text = "\n".join(r._mapping["chunk"] for r in reversed(output_rows))
                # Strip any residual stream-json lines stored before the parser was added
                cleaned = _clean_agent_output(raw_text)

                # Fallback: if agent_output was empty/garbage, check project_context
                if cleaned == "No output captured." or not cleaned.strip():
                    ctx_row = conn.exec_driver_sql(
                        "SELECT content FROM project_context "
                        "WHERE author_agent_id = ? ORDER BY created_at DESC LIMIT 1",
                        (aid,),
                    ).fetchone()
                    if ctx_row:
                        cleaned = ctx_row._mapping["content"]

                agent_dict["output"] = cleaned
            else:
                agent_dict["output"] = None

            if agent_dict["status"] in ("running", "paused"):
                all_completed = False
                any_running = True
            elif agent_dict["status"] in ("idle",):
                all_completed = False

            agents_info.append(agent_dict)

        result["agents"] = agents_info

        if all_completed and result["status"] == "running":
            summaries: list[str] = []
            for ai in agents_info:
                if ai.get("output"):
                    role_label = (ai.get("role") or "agent").replace("-", " ").title()
                    summaries.append(f"## {role_label} ({ai['name']})\n\n{ai['output']}")
            results_summary = "\n\n---\n\n".join(summaries) if summaries else "No output captured."

            conn.execute(
                update(analysis_jobs)
                .where(analysis_jobs.c.id == job_id)
                .values(status="completed", results_summary=results_summary)
            )
            conn.execute(
                update(analysis_jobs)
                .where(analysis_jobs.c.id == job_id)
                .values(completed_at=now())
            )
            result["status"] = "completed"
            result["results_summary"] = results_summary

        return result


@router.get("/api/analysis-jobs")
def list_analysis_jobs(node_id: str | None = None):
    """List analysis jobs, optionally filtered by node_id."""
    with get_db() as conn:
        if node_id:
            rows = conn.execute(
                select(analysis_jobs)
                .where(analysis_jobs.c.node_id == node_id)
                .order_by(analysis_jobs.c.created_at.desc())
            ).fetchall()
        else:
            rows = conn.execute(
                select(analysis_jobs)
                .order_by(analysis_jobs.c.created_at.desc())
                .limit(50)
            ).fetchall()

        results = []
        for row in rows:
            d = dict(row._mapping)
            d["agent_ids"] = json.loads(d.get("agent_ids", "[]"))
            results.append(d)

        return results


# ---------------------------------------------------------------------------
# Post-analysis actions
# ---------------------------------------------------------------------------

from pydantic import BaseModel


class GenerateDocumentBody(BaseModel):
    document_type: str  # "prd", "status-report", "executive-summary"


@router.post("/api/analysis-jobs/{job_id}/extract-todos")
def extract_todos_from_analysis(job_id: str):
    """Extract action items / todos from analysis results and create platform todos."""
    with get_db() as conn:
        job = conn.execute(
            select(analysis_jobs).where(analysis_jobs.c.id == job_id)
        ).fetchone()
        if not job:
            raise HTTPException(404, "Analysis job not found")

        agent_ids = json.loads(job._mapping.get("agent_ids", "[]"))
        node_id = job._mapping.get("node_id")

        # Gather all agent output
        all_output = []
        for aid in agent_ids:
            output_rows = conn.exec_driver_sql(
                "SELECT chunk FROM agent_output WHERE agent_id = ? ORDER BY id LIMIT 200",
                (aid,),
            ).fetchall()
            raw = "\n".join(r._mapping["chunk"] for r in output_rows)
            cleaned = _clean_agent_output(raw)
            if cleaned and cleaned != "No output captured.":
                all_output.append(cleaned)

        # Also check project_context
        if not all_output:
            ctx_rows = conn.exec_driver_sql(
                "SELECT content FROM project_context WHERE node_id = ? ORDER BY created_at DESC LIMIT 5",
                (node_id,),
            ).fetchall()
            for r in ctx_rows:
                if r._mapping["content"]:
                    all_output.append(r._mapping["content"])

        if not all_output:
            return {"created": 0, "message": "No analysis output to extract from"}

        combined = "\n\n---\n\n".join(all_output)

        # Use simple regex extraction for action items
        todo_patterns = [
            r'- \[ \] (.+)',               # Markdown checkbox
            r'- \*\*(.+?)\*\*',            # Bold list items
            r'(?:TODO|Action|Next step)[:\s]+(.+)',  # Explicit labels
        ]

        items: list[str] = []
        for pattern in todo_patterns:
            items.extend(re.findall(pattern, combined, re.IGNORECASE))

        # Deduplicate (rough)
        seen: set[str] = set()
        unique_items: list[str] = []
        for item in items:
            item = item.strip().rstrip('*').strip()
            if len(item) < 10 or item.lower() in seen:
                continue
            seen.add(item.lower())
            unique_items.append(item)

        # Create todos in platform DB
        created = 0
        for title in unique_items[:20]:  # Cap at 20
            todo_id = str(uuid.uuid4())
            conn.execute(
                insert(hub_todos).values(
                    id=todo_id,
                    title=title[:200],
                    project_id=_get_project_for_node(conn, node_id),
                    owner="rijul",
                    priority="medium",
                    status="open",
                    source_type="analysis",
                    created_at=now(),
                )
            )
            created += 1

        return {"created": created, "items": unique_items[:20]}


@router.post("/api/analysis-jobs/{job_id}/generate-document")
def generate_document_from_analysis(job_id: str, body: GenerateDocumentBody):
    """Spawn an agent to generate a document (PRD, status report, etc.) from analysis results."""
    with get_db() as conn:
        job = conn.execute(
            select(analysis_jobs).where(analysis_jobs.c.id == job_id)
        ).fetchone()
        if not job:
            raise HTTPException(404, "Analysis job not found")

        job_data = dict(job._mapping)
        node_id = job_data.get("node_id")
        folder_path = job_data.get("folder_path")
        agent_ids = json.loads(job_data.get("agent_ids", "[]"))

        # Gather analysis output for context
        all_output: list[str] = []
        for aid in agent_ids:
            output_rows = conn.exec_driver_sql(
                "SELECT chunk FROM agent_output WHERE agent_id = ? ORDER BY id LIMIT 200",
                (aid,),
            ).fetchall()
            raw = "\n".join(r._mapping["chunk"] for r in output_rows)
            cleaned = _clean_agent_output(raw)
            if cleaned and cleaned != "No output captured.":
                all_output.append(cleaned)

        # Fallback to project_context
        if not all_output and node_id:
            ctx_rows = conn.exec_driver_sql(
                "SELECT content, section FROM project_context WHERE node_id = ? ORDER BY created_at DESC LIMIT 5",
                (node_id,),
            ).fetchall()
            for r in ctx_rows:
                if r._mapping["content"]:
                    all_output.append(f"## {r._mapping['section']}\n\n{r._mapping['content']}")

        if not all_output:
            raise HTTPException(400, "No analysis output available to generate from")

        context = "\n\n---\n\n".join(all_output)

        # Build document generation prompt
        DOC_PROMPTS = {
            "prd": (
                "Based on the following project analysis, create a comprehensive Product Requirements Document (PRD). Include:\n"
                "1. Executive Summary\n2. Problem Statement\n3. Goals & Success Metrics\n4. User Stories / Requirements\n"
                "5. Technical Requirements\n6. Dependencies & Risks\n7. Timeline & Milestones\n8. Open Questions\n\n"
                "Write it as a polished, stakeholder-ready document in Markdown format."
            ),
            "status-report": (
                "Based on the following project analysis, create a concise weekly status report. Include:\n"
                "1. Summary (3 bullets)\n2. Completed This Week\n3. In Progress\n4. Blocked / At Risk\n"
                "5. Key Decisions Needed\n6. Next Week's Priorities\n\n"
                "Format for executive audience — clear, concise, actionable."
            ),
            "executive-summary": (
                "Based on the following project analysis, create a 1-page executive summary. Include:\n"
                "1. Project Overview (2-3 sentences)\n2. Current Status (RAG)\n3. Key Risks (top 3)\n"
                "4. Decisions Required\n5. Next Steps\n\n"
                "Maximum 500 words. Write for C-level audience."
            ),
        }

        prompt_prefix = DOC_PROMPTS.get(body.document_type, DOC_PROMPTS["status-report"])
        task = f"{prompt_prefix}\n\n---\n\n## Analysis Context\n\n{context}"

        # Find an available agent for this node, or use the first one
        available_agent_id = None
        for aid in agent_ids:
            agent_row = conn.exec_driver_sql(
                "SELECT id, status FROM agents WHERE id = ? AND status IN ('idle', 'completed', 'failed')",
                (aid,),
            ).fetchone()
            if agent_row:
                available_agent_id = agent_row._mapping["id"]
                break

        if not available_agent_id:
            # Create a new agent for this task
            available_agent_id = str(uuid.uuid4())
            conn.execute(
                insert(agents).values(
                    id=available_agent_id,
                    node_id=node_id,
                    name=f"Doc Writer ({body.document_type})",
                    role="scribe",
                    status="idle",
                    model="sonnet",
                    task_description=f"Generate {body.document_type} from analysis",
                    created_at=now(),
                )
            )

    # Spawn the agent
    pid = process_manager.spawn(
        agent_id=available_agent_id,
        task=task,
        cwd=folder_path,
        model="sonnet",
        node_id=node_id,
        role="scribe",
    )

    return {
        "agent_id": available_agent_id,
        "document_type": body.document_type,
        "pid": pid,
        "status": "spawned",
    }


def _get_project_for_node(conn, node_id: str) -> str | None:
    """Look up which project a node belongs to."""
    if not node_id:
        return None
    row = conn.exec_driver_sql(
        "SELECT project_id FROM nodes WHERE id = ?", (node_id,),
    ).fetchone()
    return row._mapping["project_id"] if row else None
