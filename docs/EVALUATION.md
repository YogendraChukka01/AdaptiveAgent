# AdaptiveAgent Evaluation Plan

AdaptiveAgent is intended to be evaluated as an engineering system, not only as a demo. This document defines a reproducible evaluation framework for retrieval quality, answer quality, safety, latency, and reliability.

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

Every evaluation run should compare AdaptiveAgent against at least one simpler baseline, for example:

- Basic vector retrieval + generation
- Hybrid retrieval without reranking
- AdaptiveAgent with reranking and evaluation enabled

Do not publish benchmark numbers until the experiment has been run and the configuration is recorded.

## Dataset format

Evaluation datasets should contain reproducible question/answer/evidence records. A minimal JSONL record can look like:

```json
{"id":"q001","question":"...","reference_answer":"...","relevant_documents":["doc-12","doc-18"]}
```

Keep private or copyrighted evaluation data outside the repository unless redistribution is permitted.

## Experiment record

For every published result, record:

- Git commit or release version
- Dataset version
- Embedding model
- Reranker model
- Generator model
- Retrieval configuration
- Top-K values
- Evaluation configuration
- Hardware/runtime environment
- Number of examples
- Timestamp

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

## Next implementation steps

- [ ] Add a versioned evaluation dataset.
- [ ] Add automated retrieval metrics.
- [ ] Add generation/evidence evaluation.
- [ ] Add baseline comparison scripts.
- [ ] Export machine-readable evaluation results.
- [ ] Publish results with release notes.
