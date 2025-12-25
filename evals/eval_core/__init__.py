"""Extensible evaluation primitives."""

from .cases import EvalCase, EvalCaseSet
from .metrics import Metric, MetricResult
from .runners import EvalRunner, EvalRunResult
from .reporting import Report, ReportRenderer
from .registry import Registry

__all__ = [
    "EvalCase",
    "EvalCaseSet",
    "EvalRunner",
    "EvalRunResult",
    "Metric",
    "MetricResult",
    "Registry",
    "Report",
    "ReportRenderer",
]
