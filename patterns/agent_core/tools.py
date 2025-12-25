"""Tool interfaces and registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
import time


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    name: str
    output: Any
    is_error: bool = False
    error: Optional[str] = None
    duration_ms: Optional[int] = None


@dataclass
class ToolSpec:
    """JSON-serializable tool metadata for model/tool discovery."""

    name: str
    description: str
    args_schema: Dict[str, Any]


class Tool(Protocol):
    spec: ToolSpec

    def __call__(self, **kwargs: Any) -> Any:
        ...


class ToolRegistry:
    def __init__(self, tools: List[Tool]):
        self._tools: Dict[str, Tool] = {t.spec.name: t for t in tools}

    def list_specs(self) -> List[ToolSpec]:
        return [t.spec for t in self._tools.values()]

    def has(self, name: str) -> bool:
        return name in self._tools

    def call(self, name: str, args: Dict[str, Any]) -> ToolResult:
        if name not in self._tools:
            return ToolResult(name=name, output=None, is_error=True, error=f"Unknown tool: {name}")

        tool = self._tools[name]
        start = time.time()
        try:
            out = tool(**args)
            dur_ms = int((time.time() - start) * 1000)
            return ToolResult(name=name, output=out, duration_ms=dur_ms)
        except Exception as exc:
            dur_ms = int((time.time() - start) * 1000)
            return ToolResult(name=name, output=None, is_error=True, error=str(exc), duration_ms=dur_ms)
