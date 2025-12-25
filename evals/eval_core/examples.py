"""Example metrics and usage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .cases import EvalCase, EvalCaseSet
from .metrics import Metric, MetricResult
from .runners import EvalRunner
from .reporting import Report, ReportRenderer


@dataclass
class ExactMatchMetric:
    name: str = "exact_match"

    def evaluate(self, *, output: Dict[str, Any], expected: Dict[str, Any], context: Dict[str, Any]) -> MetricResult:
        value = 1.0 if output == expected else 0.0
        return MetricResult(name=self.name, score=value, details={"output": output, "expected": expected})


def dummy_predictor(inputs: Dict[str, Any]) -> Dict[str, Any]:
    return {"answer": inputs.get("answer", None)}


def run_example() -> str:
    dataset = EvalCaseSet.from_iterable(
        "toy",
        [
            EvalCase(id="1", input={"answer": "a"}, expected={"answer": "a"}),
            EvalCase(id="2", input={"answer": "b"}, expected={"answer": "c"}),
        ],
    )

    runner = EvalRunner(predictor=dummy_predictor)
    result = runner.run(dataset, metrics=[ExactMatchMetric()])

    summary = {
        name: sum(r.score for r in results) / max(len(results), 1)
        for name, results in result.metric_results.items()
    }
    report = Report(dataset=result.dataset, summary=summary, raw=result.metric_results)

    return ReportRenderer().render_text(report)
