"""Metric definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass
class MetricResult:
    name: str
    score: float
    details: Dict[str, Any]


class Metric(Protocol):
    name: str

    def evaluate(self, *, output: Dict[str, Any], expected: Dict[str, Any], context: Dict[str, Any]) -> MetricResult:
        ...
