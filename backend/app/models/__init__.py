"""Centralized Pydantic models for the CoCo Platform API."""

# Common / shared
from app.models.common import TransitionBody

# Agents
from app.models.agents import (
    CreateAgentBody,
    CreateRoleBody,
    PatchAgentBody,
    RecruitAgentBody,
    SpawnAgentBody,
)

# Tasks
from app.models.tasks import CheckoutTaskBody, CreateTaskBody, PatchTaskBody

# Todos
from app.models.todos import CreateTodoBody, MergeTodosBody, PatchTodoBody

# Goals
from app.models.goals import GoalCreate, GoalUpdate

# Chat
from app.models.chat import ChatRequest, MessageOut, SessionCreate, SessionOut

# Tree
from app.models.tree import CreateNodeBody, MoveNodeBody, PatchNodeBody, ReorderItem

# Collaboration
from app.models.collaboration import (
    CreateContextBody,
    CreateHandoffBody,
    PatchContextBody,
    PatchHandoffBody,
    PatchWorkflowBody,
    StartWorkflowBody,
)

# Comments
from app.models.comments import CreateCommentBody, PatchCommentBody

# Templates
from app.models.templates import ImportTemplateBody, SaveTemplateBody

# Analysis
from app.models.analysis import AnalyzeFolderBody

# Jarvis
from app.models.jarvis import (
    CardActionModel,
    CardDataModel,
    CommandRequest,
    CommandResponse,
)

# TTS
from app.models.tts import TTSRequest

# Costs
from app.models.costs import CreateBudgetBody

# Content
from app.models.content import ClassifyContentBody

# Settings
from app.models.settings import UpdateSettingsBody

# Brain / People
from app.models.brain import UpdatePersonBody

# Projects
from app.models.projects import ProjectUpdate

# Self-Improve
from app.models.self_improve import StartCycleBody, ApproveImprovementBody, RejectImprovementBody

__all__ = [
    # Common
    "TransitionBody",
    # Agents
    "CreateAgentBody",
    "CreateRoleBody",
    "PatchAgentBody",
    "RecruitAgentBody",
    "SpawnAgentBody",
    # Tasks
    "CheckoutTaskBody",
    "CreateTaskBody",
    "PatchTaskBody",
    # Todos
    "CreateTodoBody",
    "MergeTodosBody",
    "PatchTodoBody",
    # Goals
    "GoalCreate",
    "GoalUpdate",
    # Chat
    "ChatRequest",
    "MessageOut",
    "SessionCreate",
    "SessionOut",
    # Tree
    "CreateNodeBody",
    "MoveNodeBody",
    "PatchNodeBody",
    "ReorderItem",
    # Collaboration
    "CreateContextBody",
    "CreateHandoffBody",
    "PatchContextBody",
    "PatchHandoffBody",
    "PatchWorkflowBody",
    "StartWorkflowBody",
    # Comments
    "CreateCommentBody",
    "PatchCommentBody",
    # Templates
    "ImportTemplateBody",
    "SaveTemplateBody",
    # Analysis
    "AnalyzeFolderBody",
    # Jarvis
    "CardActionModel",
    "CardDataModel",
    "CommandRequest",
    "CommandResponse",
    # TTS
    "TTSRequest",
    # Costs
    "CreateBudgetBody",
    # Content
    "ClassifyContentBody",
    # Settings
    "UpdateSettingsBody",
    # Brain
    "UpdatePersonBody",
    # Projects
    "ProjectUpdate",
    # Self-Improve
    "StartCycleBody",
    "ApproveImprovementBody",
    "RejectImprovementBody",
]
