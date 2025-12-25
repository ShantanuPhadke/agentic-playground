"""Model interface protocol."""

from __future__ import annotations

from typing import List, Optional, Protocol

from .messages import Message, ModelResponse


class ChatModel(Protocol):
    """Implement for any provider that can accept messages and return text."""

    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.2,
        max_tokens: int = 800,
        json_mode: bool = False,
        stop: Optional[List[str]] = None,
        timeout_s: Optional[float] = None,
    ) -> ModelResponse:
        ...
