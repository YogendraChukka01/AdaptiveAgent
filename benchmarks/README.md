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
8. Review failures and outliers.
9. Update the report and release notes.
