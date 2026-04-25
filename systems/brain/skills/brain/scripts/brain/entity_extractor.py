"""
Brain Entity Extractor — Extracts entity names from plain text.

Uses regex patterns and heuristics to find:
- Person names (First Last, First M. Last)
- System/tool names (capitalized multi-word or known patterns)
- Team/org names (... Team, ... Group, ... Committee)

No LLM calls — pure pattern matching for speed in automated pipelines.
"""

import re
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Known system/tool names (project-specific catalog — extend as needed)
KNOWN_SYSTEMS = {
    "ServiceNow", "Snowflake",
    "Kafka", "DynamoDB",
    "Tableau", "SAP", "Jira", "Confluence", "Slack", "Teams",
    "AWS", "Azure", "GCP", "Lambda", "S3", "EKS", "RDS",
    "Power BI", "SharePoint", "Excel", "PowerPoint",
    # populate with project-specific tools as needed
}

# Team/group suffixes
_TEAM_SUFFIXES = re.compile(
    r'\b([A-Z][a-zA-Z\s&-]{2,30}\s+'
    r'(?:Team|Group|Committee|Board|Council|Office|Unit|Division|Department|Squad|Pod))\b'
)

# Person name patterns
_PERSON_NAME = re.compile(
    r'\b([A-Z][a-z]{1,15}\s+'           # First name
    r'(?:[A-Z]\.?\s+)?'                  # Optional middle initial
    r'[A-Z][a-z]{1,20})'                 # Last name
    r'(?:\s|[,.\;:!?\)\]\n]|$)'           # Word boundary
)

# Email addresses -> extract person name
_EMAIL_FROM = re.compile(
    r'(?:From|To|Cc|from|to|cc):\s*'
    r'([A-Z][a-z]+\s+[A-Z][a-z]+)'      # Name before email
)

# Role patterns
_ROLE_PATTERN = re.compile(
    r'\b([A-Z][a-zA-Z\s]{2,30}\s+'
    r'(?:Manager|Director|Lead|Head|VP|Chief|Officer|Analyst|Engineer|Architect|Specialist|Consultant|Partner))\b'
)

# Words to exclude from person names (common false positives)
_EXCLUDE_NAMES = {
    "The", "This", "That", "These", "Those", "There", "Their",
    "What", "When", "Where", "Which", "While", "With",
    "From", "Into", "Upon", "About", "After", "Before",
    "Each", "Every", "Other", "Another", "Between",
    "Data Mapping", "Risk Assessment", "Due Diligence",
    "Third Party", "Risk Mgmt", "Key Features",
    "New York", "United States", "North America",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "Executive Summary", "Table Contents", "Action Items",
    "Next Steps", "Open Questions", "Meeting Notes",
    # Common verb phrases that look like "First Last"
    "Use Snowflake", "Use Lambda", "Use Azure", "Use Teams",
    "Risk Engineering", "Risk Assessment", "Risk Management",
    "Data Engineering", "Data Migration", "Data Warehouse",
    "Project Manager", "Product Owner", "Service Manager",
}

# Words that appear in business/tech terms but NOT in human names.
# If ANY word in the candidate matches this set, it's not a person.
_NON_PERSON_WORDS = {
    # Technical / IT
    "access", "action", "active", "admin", "agenda", "alert", "analytics",
    "api", "app", "approval", "archive", "assessment", "async", "audit",
    "authentication", "authorization", "automated", "automation",
    "backup", "batch", "board", "build", "bulk", "business",
    "cache", "case", "center", "change", "check", "cleanup", "client",
    "cloud", "code", "compliance", "component", "compute", "config",
    "configuration", "connect", "connection", "console", "context",
    "control", "controls", "corporate", "criteria", "critical", "cron",
    "custom", "cycle",
    "dashboard", "data", "database", "default", "deploy", "deployment",
    "design", "detail", "details", "detection", "development", "device",
    "diagrams", "digital", "display", "document", "domain", "download",
    "draft", "drafts", "dynamic",
    "email", "enable", "encryption", "endpoint", "engine", "enterprise",
    "entity", "environment", "error", "event", "evidence", "exception",
    "execution", "existing", "export", "external",
    "feature", "features", "feed", "field", "file", "filter", "final",
    "findings", "firewall", "flow", "folder", "form", "format",
    "framework", "frequency", "frontend", "full", "function", "future",
    "gateway", "general", "generation", "global", "governance", "graph",
    "group",
    "handler", "health", "help", "hierarchy", "high", "historical",
    "holding", "hub",
    "identity", "impact", "implementation", "import", "incident",
    "index", "info", "information", "infrastructure", "initial",
    "initiatives", "input", "insight", "instance", "integration",
    "intelligence", "interface", "internal", "inventory", "investigation",
    "key", "knowledge",
    "lambda", "landing", "launch", "layer", "legacy", "level", "library",
    "lifecycle", "link", "list", "load", "local", "log", "logging",
    "login", "logic", "low",
    "machine", "main", "management", "manual", "mapping", "master",
    "medium", "memory", "merge", "message", "metadata", "method",
    "metrics", "migration", "model", "models", "module", "modules",
    "monitor", "monitoring",
    "network", "node", "notification",
    "object", "onboarding", "open", "operation", "operations", "option",
    "order", "org", "organization", "output", "overview",
    "package", "page", "panel", "parameter", "patch", "path", "pattern",
    "payload", "pending", "performance", "permission", "permissions",
    "phase", "phased", "pipeline", "plan", "planned", "planning",
    "platform", "plugin", "point", "policy", "policies", "pool",
    "portal", "portfolio", "post", "practice", "pricing", "primary",
    "priority", "private", "process", "processes", "processing",
    "product", "production", "profile", "program", "project", "projects",
    "proposed", "protection", "protocol", "provider", "provisioning",
    "public", "push",
    "quality", "query", "queue",
    "rate", "real", "reason", "reasoning", "record", "records",
    "recovery", "reference", "refresh", "regional", "register",
    "registry", "regulatory", "release", "remediation", "remote",
    "removal", "report", "reports", "repository", "request", "required",
    "requirements", "resolution", "resource", "response", "result",
    "results", "retention", "review", "reviews", "revised", "risk",
    "risks", "roadmap", "role", "roles", "rollback", "rollout", "root",
    "routing", "rule", "rules", "run", "runtime",
    "scan", "scanning", "scenario", "schedule", "schema", "scope",
    "score", "script", "search", "secret", "section", "security",
    "server", "service", "services", "session", "setting", "settings",
    "setup", "severity", "shared", "sharing", "shell", "signal",
    "single", "site", "snapshot", "solution", "source", "specification",
    "sprint", "stack", "stage", "standard", "standards", "start",
    "state", "status", "step", "storage", "strategy", "stream",
    "structure", "stub", "submission", "subscribe", "summary",
    "support", "survey", "switch", "sync", "system", "systems",
    "table", "tag", "target", "task", "tasks", "template", "tenant",
    "test", "testing", "thread", "threshold", "ticket", "tier",
    "timeline", "token", "tool", "tools", "total", "tracking",
    "traffic", "training", "transaction", "transfer", "transform",
    "trigger", "type",
    "unit", "update", "upgrade", "upload", "usage", "user",
    "validation", "value", "variable", "vendor", "verification",
    "version", "view", "virtual", "vision", "volume",
    "warning", "watch", "web", "webhook", "weekly", "widget",
    "window", "wizard", "work", "workflow", "workflows", "working",
    "workspace", "wrapper",
    # Verbs commonly appearing at start of "First Last" false positives
    "add", "added", "adding", "address", "addressed", "analyze",
    "apply", "assign", "attach", "attempt",
    "begin", "browse",
    "calculate", "call", "cancel", "capture", "carry", "close",
    "collect", "combine", "compare", "complete", "configure",
    "confirm", "consider", "contain", "continue", "convert",
    "copy", "correct", "cover", "create",
    "define", "delete", "deliver", "describe", "detect",
    "determine", "disable", "discuss", "download", "drive",
    "edit", "eliminate", "embed", "enforce", "ensure",
    "enter", "establish", "evaluate", "examine", "exclude",
    "execute", "expand", "expect", "explain", "extend", "extract",
    "facilitate", "fetch", "fill", "fix", "follow", "generate",
    "handle", "identify", "implement", "include", "increase",
    "indicate", "initiate", "insert", "inspect", "install",
    "integrate", "introduce", "investigate",
    "keep",
    "leverage", "limit", "link", "locate",
    "maintain", "manage", "map", "mark", "match", "measure",
    "modify", "move",
    "notify",
    "obtain", "operate", "optimize", "outline", "override",
    "parse", "perform", "permit", "place", "populate", "prepare",
    "present", "prevent", "prioritize", "proceed", "produce",
    "propose", "protect", "provide", "publish", "pull",
    "raise", "reach", "receive", "recommend", "reduce", "refine",
    "register", "reject", "release", "remove", "rename", "render",
    "replace", "replicate", "require", "reset", "resolve",
    "restart", "restore", "restrict", "retrieve", "return", "revert",
    "revise", "rotate", "route", "run",
    "save", "scale", "schedule", "secure", "select", "send",
    "separate", "serve", "set", "share", "show", "shut", "sign",
    "simplify", "skip", "sort", "specify", "split", "stage",
    "standardize", "start", "stop", "store", "stream", "submit",
    "subscribe", "suggest", "summarize", "supply", "suspend",
    "take", "terminate", "toggle", "trace", "track", "transfer",
    "translate", "trigger", "troubleshoot", "turn",
    "unblock", "undo", "unify", "unlink", "unlock",
    "upgrade", "upload", "use", "utilize",
    "validate", "verify", "view",
    "wait", "write",
}


def _normalize_text_for_ner(text: str) -> str:
    """Flatten whitespace before entity extraction.

    The regex patterns below all use ``\\s+`` which matches newlines and
    tabs.  That lets "Compliance\\nRobert" (a section header followed by
    the first word of the next paragraph) match the person name pattern
    and get stored as a single entity.  After the flatten step, the
    regexes only see a single space and the boundary logic works
    correctly.

    Preserves sentence boundaries by keeping exactly one space between
    every token run, so downstream readers don't lose context.
    """
    if not text:
        return text
    # Collapse any run of [\n\t\r\f\v ] into a single space, keep other chars intact.
    return re.sub(r"[\r\n\t\f\v ]+", " ", text)


def extract_entities(text: str, project_slug: str = "") -> list[dict]:
    """Extract entity candidates from plain text.

    Returns list of dicts: {name, type, confidence, source}
    Types: person, system, team, role
    Confidence: 0.0-1.0 (higher = more certain)
    """
    if not text or len(text) < 10:
        return []

    # Layer 1 fix (2026-04-22): normalize whitespace before pattern matching.
    # Prior runs produced entities like "Compliance\nRobert" because the
    # regexes' ``\\s+`` span leaked across newlines.  Flatten first.
    text = _normalize_text_for_ner(text)

    entities: dict[str, dict] = {}  # name -> entity dict (dedup by name)

    # 1. Known systems (highest confidence)
    text_upper = text.upper()
    for system in KNOWN_SYSTEMS:
        if system.upper() in text_upper:
            # Verify it's a word boundary match
            if re.search(r'\b' + re.escape(system) + r'\b', text, re.IGNORECASE):
                entities[system] = {
                    "name": system,
                    "type": "system",
                    "confidence": 0.95,
                    "source": f"known_system:{project_slug}",
                }

    # 2. Team/group names
    for match in _TEAM_SUFFIXES.finditer(text):
        name = match.group(1).strip()
        # Strip leading "The " for cleaner entity names
        if name.startswith("The "):
            name = name[4:]
        if name not in _EXCLUDE_NAMES and len(name) > 5:
            entities[name] = {
                "name": name,
                "type": "team",
                "confidence": 0.7,
                "source": f"team_pattern:{project_slug}",
            }

    # 3. Person names (with strict validation to reject business/tech terms)
    for match in _PERSON_NAME.finditer(text):
        name = match.group(1).strip()
        if name in _EXCLUDE_NAMES:
            continue
        if any(w in name for w in ["The ", "This ", "That "]):
            continue
        parts = name.split()
        # Both parts must be title case, not ALL CAPS
        if not all(p[0].isupper() and not p.isupper() for p in parts):
            continue
        # Reject if ANY word is a known non-person word (business/tech term)
        if any(p.lower() in _NON_PERSON_WORDS for p in parts):
            continue
        # Reject names with newlines (document parsing artifacts)
        if "\n" in name or "\t" in name:
            continue
        # Reject single-char or 2-char words that aren't initials (Ad, On, Or)
        if any(len(p) <= 2 and p[1:].islower() for p in parts):
            continue
        entities.setdefault(name, {
            "name": name,
            "type": "person",
            "confidence": 0.6,
            "source": f"name_pattern:{project_slug}",
        })

    # 4. Email-derived names
    for match in _EMAIL_FROM.finditer(text):
        name = match.group(1).strip()
        if name not in _EXCLUDE_NAMES:
            entities.setdefault(name, {
                "name": name,
                "type": "person",
                "confidence": 0.8,
                "source": f"email_header:{project_slug}",
            })

    # 5. Role patterns (lower confidence -- might be descriptions, not entity names)
    for match in _ROLE_PATTERN.finditer(text):
        name = match.group(1).strip()
        if name not in _EXCLUDE_NAMES and len(name) > 8:
            entities.setdefault(name, {
                "name": name,
                "type": "role",
                "confidence": 0.4,
                "source": f"role_pattern:{project_slug}",
            })

    # 6. Dedup: remove person/role candidates that are substrings of
    #    higher-confidence entities (teams, systems)
    high_conf_names = {
        e["name"] for e in entities.values()
        if e["type"] in ("system", "team") and e["confidence"] >= 0.7
    }
    to_remove = []
    for name, ent in entities.items():
        if ent["type"] in ("person", "role"):
            for hc_name in high_conf_names:
                if name != hc_name and name in hc_name:
                    to_remove.append(name)
                    break
    for name in to_remove:
        del entities[name]

    # Layer 2 fix (2026-04-22): defense-in-depth sanitizer.  Even after the
    # input-normalization step, a pattern might still capture a name with
    # embedded whitespace (e.g. email headers that already contain \n).
    # Drop any entity whose name has control chars, multi-space runs, or
    # degenerate length after strip.
    sanitized: dict[str, dict] = {}
    for name, ent in entities.items():
        clean = re.sub(r"\s+", " ", name).strip()
        if not clean or len(clean) < 2 or len(clean) > 80:
            continue
        if "\n" in name or "\t" in name:
            # Try to recover by taking the first word-or-phrase segment
            parts = [p.strip() for p in re.split(r"[\n\t]+", name) if len(p.strip()) >= 3]
            if not parts:
                continue
            clean = parts[0]  # keep only the leading clean part
        if clean != name:
            ent = dict(ent)
            ent["name"] = clean
            ent["source"] = ent.get("source", "") + ":sanitized"
        sanitized[clean] = ent

    result = sorted(sanitized.values(), key=lambda e: -e["confidence"])
    log.debug("Extracted %d entities from %d chars of text", len(result), len(text))
    return result
