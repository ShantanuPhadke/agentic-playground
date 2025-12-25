"""Registry for metrics and datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .cases import EvalCaseSet
from .metrics import Metric


@dataclass
class Registry:
    metrics: Dict[str, Metric] = field(default_factory=dict)
    datasets: Dict[str, EvalCaseSet] = field(default_factory=dict)

    def register_metric(self, metric: Metric) -> None:
        self.metrics[metric.name] = metric

    def register_dataset(self, dataset: EvalCaseSet) -> None:
        self.datasets[dataset.name] = dataset

    def list_metrics(self) -> List[str]:
        return sorted(self.metrics.keys())

    def list_datasets(self) -> List[str]:
        return sorted(self.datasets.keys())

    def get_metric(self, name: str) -> Metric:
        return self.metrics[name]

    def get_dataset(self, name: str) -> EvalCaseSet:
        return self.datasets[name]
