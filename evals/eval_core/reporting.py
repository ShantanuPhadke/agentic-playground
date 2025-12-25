"""Report rendering for eval runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .metrics import MetricResult


@dataclass
class Report:
    dataset: str
    summary: Dict[str, float]
    raw: Dict[str, List[MetricResult]]


class ReportRenderer:
    def render_text(self, report: Report) -> str:
        lines = [f"Dataset: {report.dataset}", "", "Summary:"]
        for metric_name, score in sorted(report.summary.items()):
            lines.append(f"- {metric_name}: {score:.3f}")
        return "\n".join(lines)
