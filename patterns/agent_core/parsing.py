"""Provider-agnostic parsing for tool call plans."""

from __future__ import annotations

from typing import List, Optional, Tuple
import json

from .tools import ToolCall

TOOL_CALL_INSTRUCTIONS = """
If you need to use a tool, respond ONLY with a JSON object in this format:

{
  "tool_calls": [
    {"name": "<tool_name>", "arguments": { ... }},
    ...
  ],
  "final": "<optional final user-facing text if no further tools needed>"
}

Rules:
- If calling tools, include them in tool_calls.
- If no tools are needed, return tool_calls as [] and put the final answer in "final".
- Do not include any other keys.
"""


def parse_tool_plan(text: str) -> Tuple[List[ToolCall], Optional[str]]:
    """Parse a tool plan from raw model text."""

    try:
        obj = json.loads(text)
        tool_calls = [ToolCall(name=t["name"], arguments=t.get("arguments", {})) for t in obj.get("tool_calls", [])]
        final = obj.get("final")
        return tool_calls, final
    except Exception:
        return [], text
