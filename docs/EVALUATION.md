# AdaptiveAgent Evaluation Plan

AdaptiveAgent is evaluated as an engineering system, not only as a demo. The goal is to make retrieval quality, answer quality, safety, latency, and reliability measurable and comparable between versions.

## Evaluation goals

1. Measure whether retrieval returns useful evidence.
2. Measure whether generated answers are grounded in retrieved evidence.
3. Measure answer relevance and completeness.
4. Measure the effect of reranking and the adaptive/refine loop.
5. Measure latency and failure behavior.
6. Make changes comparable across versions.

## Metrics

### Retrieval

- Recall@K
- Precision@K
- MRR
- nDCG@K

### Generation

- Faithfulness / groundedness
- Answer relevancy
- Context precision
- Context recall
- Citation/evidence coverage

### System

- End-to-end latency (p50/p95)
- Retrieval latency
- Generation latency
- Error rate
- Retry/refine rate
- Token usage where available

## Baselines

Every evaluation run should compare AdaptiveAgent against at least one simpler baseline:

- Basic vector retrieval + generation
- Hybrid retrieval without reranking
- AdaptiveAgent with reranking and evaluation enabled

Do not publish benchmark numbers until the experiment has actually run and the configuration is recorded.

## Dataset

A small, redistributable smoke-test dataset is provided at [`benchmarks/dataset.sample.jsonl`](../benchmarks/dataset.sample.jsonl). It validates the evaluation workflow and expected dataset schema; it is **not** a performance benchmark and must not be presented as one.

For meaningful results, use a larger versioned dataset with manually reviewed relevance labels and reference answers.

## Result format

For every published result, record:

- Git commit or release version
- Dataset version
- Embedding model
- Reranker model
- Generator model
- Judge model, when applicable
- Retrieval configuration
- Top-K values
- Evaluation configuration
- Hardware/runtime environment
- Number of examples
- Timestamp

Store machine-readable results under `benchmarks/results/` when results are available. Do not commit secrets or private evaluation data.

## Reporting template

| Metric | Baseline | AdaptiveAgent | Delta |
|---|---:|---:|---:|
| Recall@5 | TBD | TBD | TBD |
| MRR | TBD | TBD | TBD |
| Faithfulness | TBD | TBD | TBD |
| Answer relevancy | TBD | TBD | TBD |
| p50 latency | TBD | TBD | TBD |
| p95 latency | TBD | TBD | TBD |
| Error rate | TBD | TBD | TBD |

`TBD` values are intentional until measured. Never replace them with estimated or fabricated results.

## Regression policy

Evaluation should run before major retrieval, prompting, routing, or model changes are merged. A regression should be investigated when quality decreases materially or latency/error rate increases without an explicit trade-off.

## Reproduction workflow

1. Start the documented Docker stack.
2. Load the versioned evaluation dataset.
3. Record the exact Git commit.
4. Record embedding, reranker, generator, and judge models.
5. Run the baseline.
6. Run AdaptiveAgent with the same dataset and hardware.
7. Export machine-readable results.
8. Review failures and outliers.
9. Update the report and release notes.

## Demo and release

Use [`docs/DEMO_RUNBOOK.md`](./DEMO_RUNBOOK.md) for the public product demonstration and [`docs/RELEASE_CHECKLIST.md`](./RELEASE_CHECKLIST.md) before publishing a release.

## Status

The evaluation framework and smoke-test dataset are now in place. **Published performance numbers remain intentionally absent until real experiments are executed.**
