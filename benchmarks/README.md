# AdaptiveAgent Benchmarks

This directory contains the reproducible benchmark contract for AdaptiveAgent.

## Principles

- Never commit fabricated metrics.
- Every published result must identify the commit, dataset version, models, configuration, hardware, and timestamp.
- Compare AdaptiveAgent with a documented baseline.
- Keep private/copyrighted evaluation data out of the repository.

## Required benchmark tracks

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
- Evidence coverage

### System

- End-to-end p50/p95 latency
- Retrieval latency
- Generation latency
- Error rate
- Retry/refine rate
- Token usage where available

## Deterministic retrieval scorer

`scripts/evaluate_retrieval.py` scores an already-generated retrieval run without calling an LLM. This keeps the metric calculation deterministic.

Expected prediction format:

```json
{"id":"q001","relevant_documents":["doc-a"],"retrieved_documents":["doc-a","doc-b"]}
```

Example:

```bash
python scripts/evaluate_retrieval.py benchmarks/predictions.sample.jsonl --k 5 --output benchmarks/results.sample.json
```

The sample predictions are **fixtures for validating the scorer, not a performance claim**. Real benchmark predictions must come from an actual AdaptiveAgent run.

## Result format

Published results belong in a versioned result file such as `results/v1.1.0.json`. Do not replace `TBD` with estimates. A result is publishable only after the experiment has actually run.

## Reproduction checklist

1. Start the documented Docker stack.
2. Load the versioned evaluation dataset.
3. Record the exact Git commit.
4. Record embedding, reranker, generator and judge models.
5. Run the baseline.
6. Run AdaptiveAgent with the same dataset and hardware.
7. Export machine-readable results.
8. Score deterministic metrics with the repository scorer.
9. Review failures and outliers.
10. Update the report and release notes.
