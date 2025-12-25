"""Eval case definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping


@dataclass
class EvalCase:
    """Single evaluation input + expected outputs (if any)."""

    id: str
    input: Mapping[str, Any]
    expected: Mapping[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class EvalCaseSet:
    name: str
    cases: List[EvalCase]

    @classmethod
    def from_iterable(cls, name: str, cases: Iterable[EvalCase]) -> "EvalCaseSet":
        return cls(name=name, cases=list(cases))
