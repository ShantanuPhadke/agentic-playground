"""Execution trace utilities for debugging and evals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
import time


@dataclass
class TraceEvent:
    t: float
    kind: str
    payload: Dict[str, Any]


@dataclass
class Trace:
    events: List[TraceEvent] = field(default_factory=list)

    def add(self, kind: str, **payload: Any) -> None:
        self.events.append(TraceEvent(t=time.time(), kind=kind, payload=payload))
