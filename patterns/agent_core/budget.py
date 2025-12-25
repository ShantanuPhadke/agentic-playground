"""Budget controls for bounded execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Budget:
    max_steps: int = 8
    max_tool_calls: int = 8
    max_wall_time_s: Optional[float] = 30.0
