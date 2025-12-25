"""Message primitives shared across models and tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

Role = str  # "system" | "user" | "assistant" | "tool"


@dataclass
class Message:
    role: Role
    content: str
    name: Optional[str] = None  # tool name or assistant name
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Provider-agnostic response payload."""

    content: str
    tool_calls: list["ToolCall"] = field(default_factory=list)
    raw: Any = None


from .tools import ToolCall  # late import to avoid circular typing
