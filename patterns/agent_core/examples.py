"""Example tool + model adapter placeholders."""

from __future__ import annotations

from typing import Any, List
import json

from .agent import Agent
from .messages import Message, ModelResponse
from .tools import ToolRegistry, ToolSpec


class EchoTool:
    spec = ToolSpec(
        name="echo",
        description="Echo back the input text.",
        args_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    )

    def __call__(self, text: str) -> str:
        return text


class DummyModel:
    """Replace with a real model adapter."""

    def generate(self, messages: List[Message], **kwargs: Any) -> ModelResponse:
        return ModelResponse(content=json.dumps({"tool_calls": [], "final": "Hello from DummyModel!"}))


def run_example() -> str:
    agent = Agent(model=DummyModel(), tools=ToolRegistry([EchoTool()]))
    final, _state, _trace = agent.run("Say hello")
    return final
