"""Agent runtime built on primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple
import json
import time

from .budget import Budget
from .messages import Message, ModelResponse
from .models import ChatModel
from .parsing import TOOL_CALL_INSTRUCTIONS, parse_tool_plan
from .tools import ToolRegistry
from .trace import Trace


@dataclass
class AgentConfig:
    name: str = "agent"
    temperature: float = 0.2
    max_tokens: int = 800
    system_prompt: str = "You are a helpful agent."
    tool_prompt: str = TOOL_CALL_INSTRUCTIONS


@dataclass
class AgentState:
    """Mutable state shared across steps and patterns."""

    data: Dict[str, Any] = field(default_factory=dict)


class StopCondition(Protocol):
    def __call__(self, *, state: AgentState, last_model: Optional[ModelResponse], trace: Trace) -> bool:
        ...


def default_stop_condition(*, state: AgentState, last_model: Optional[ModelResponse], trace: Trace) -> bool:
    return "final" in state.data and state.data["final"] is not None


class Agent:
    def __init__(
        self,
        model: ChatModel,
        tools: ToolRegistry,
        *,
        config: Optional[AgentConfig] = None,
        budget: Optional[Budget] = None,
        stop_condition: StopCondition = default_stop_condition,
    ):
        self.model = model
        self.tools = tools
        self.config = config or AgentConfig()
        self.budget = budget or Budget()
        self.stop_condition = stop_condition

    def run(self, user_input: str, *, state: Optional[AgentState] = None) -> Tuple[str, AgentState, Trace]:
        state = state or AgentState()
        trace = Trace()

        start_t = time.time()
        tool_calls_used = 0
        last_model: Optional[ModelResponse] = None

        messages: List[Message] = [
            Message(role="system", content=self.config.system_prompt),
            Message(role="system", content=self.config.tool_prompt),
            Message(role="user", content=user_input),
        ]

        messages[1].metadata["tools"] = [s.__dict__ for s in self.tools.list_specs()]

        for step in range(self.budget.max_steps):
            if self.budget.max_wall_time_s is not None and (time.time() - start_t) > self.budget.max_wall_time_s:
                state.data["final"] = state.data.get("final") or "Stopped: wall-time budget exceeded."
                trace.add("stop", reason="wall_time_budget_exceeded")
                break

            last_model = self.model.generate(
                messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                json_mode=False,
            )
            trace.add("model", step=step, content=last_model.content)

            tool_calls, final_text = parse_tool_plan(last_model.content)

            if tool_calls:
                for tc in tool_calls:
                    if tool_calls_used >= self.budget.max_tool_calls:
                        state.data["final"] = "Stopped: tool-call budget exceeded."
                        trace.add("stop", reason="tool_call_budget_exceeded")
                        break

                    tool_calls_used += 1
                    trace.add("decision", action="tool_call", tool=tc.name, args=tc.arguments)

                    result = self.tools.call(tc.name, tc.arguments)
                    trace.add(
                        "tool",
                        tool=tc.name,
                        is_error=result.is_error,
                        duration_ms=result.duration_ms,
                        output_preview=str(result.output)[:500],
                        error=result.error,
                    )

                    messages.append(Message(role="assistant", content=last_model.content))
                    messages.append(
                        Message(
                            role="tool",
                            name=tc.name,
                            content=json.dumps(
                                {
                                    "output": result.output,
                                    "is_error": result.is_error,
                                    "error": result.error,
                                }
                            ),
                        )
                    )

                if "final" in state.data and state.data["final"].startswith("Stopped:"):
                    break
                continue

            if final_text is not None:
                state.data["final"] = final_text
                trace.add("decision", action="finalize")
                break

            state.data["final"] = last_model.content
            trace.add("decision", action="finalize_fallback")
            break

            # if self.stop_condition(state=state, last_model=last_model, trace=trace):
            #     break

        return state.data.get("final", ""), state, trace
