"""Execution of evals over datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List
import time

from .cases import EvalCaseSet
from .metrics import Metric, MetricResult


@dataclass
class EvalRunResult:
    dataset: str
    outputs: Dict[str, Dict[str, Any]]
    metric_results: Dict[str, List[MetricResult]]
    duration_ms: int


class EvalRunner:
    def __init__(self, *, predictor: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.predictor = predictor

    def run(
        self,
        dataset: EvalCaseSet,
        metrics: Iterable[Metric],
        *,
        context: Dict[str, Any] | None = None,
    ) -> EvalRunResult:
        ctx = context or {}
        outputs: Dict[str, Dict[str, Any]] = {}
        metric_results: Dict[str, List[MetricResult]] = {m.name: [] for m in metrics}

        start = time.time()
        for case in dataset.cases:
            output = self.predictor(dict(case.input))
            outputs[case.id] = output
            for metric in metrics:
                result = metric.evaluate(output=output, expected=dict(case.expected), context=ctx)
                metric_results[metric.name].append(result)
        duration_ms = int((time.time() - start) * 1000)

        return EvalRunResult(
            dataset=dataset.name,
            outputs=outputs,
            metric_results=metric_results,
            duration_ms=duration_ms,
        )
