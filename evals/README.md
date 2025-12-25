# Evals
Extensible evaluation scaffolding for agent behavior.

## Structure
- `eval_core/`: core primitives (datasets, metrics, runners, reporting)

## Quick start
- Implement a predictor that maps inputs to outputs.
- Define metrics with `Metric.evaluate`.
- Run `EvalRunner` on a dataset.

## Example
```python
from evals.eval_core.cases import EvalCase, EvalCaseSet
from evals.eval_core.examples import ExactMatchMetric, dummy_predictor
from evals.eval_core.reporting import Report, ReportRenderer
from evals.eval_core.runners import EvalRunner

# Build dataset
cases = [
    EvalCase(id="1", input={"answer": "a"}, expected={"answer": "a"}),
    EvalCase(id="2", input={"answer": "b"}, expected={"answer": "c"}),
]

runner = EvalRunner(predictor=dummy_predictor)
result = runner.run(EvalCaseSet.from_iterable("toy", cases), metrics=[ExactMatchMetric()])

summary = {
    name: sum(r.score for r in results) / max(len(results), 1)
    for name, results in result.metric_results.items()
}

report = Report(dataset=result.dataset, summary=summary, raw=result.metric_results)
print(ReportRenderer().render_text(report))
```
