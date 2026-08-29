#!/usr/bin/env python3
"""Compute deterministic retrieval metrics from a JSONL evaluation run.

Input records must contain:
  {"id": "q1", "relevant_documents": ["doc-a", ...], "retrieved_documents": ["doc-a", ...]}

The script deliberately does not call an LLM or invent missing predictions. It
only scores retrieval outputs that have already been produced by an experiment.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


def recall_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(relevant.intersection(retrieved[:k])) / len(relevant)


def precision_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    top = retrieved[:k]
    if not top:
        return 0.0
    return len(relevant.intersection(top)) / len(top)


def reciprocal_rank(relevant: set[str], retrieved: list[str]) -> float:
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    top = retrieved[:k]
    dcg = sum(
        (1.0 / __import__("math").log2(rank + 1))
        for rank, doc_id in enumerate(top, start=1)
        if doc_id in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / __import__("math").log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"Line {line_number}: expected a JSON object")
            for field in ("relevant_documents", "retrieved_documents"):
                if field not in record or not isinstance(record[field], list):
                    raise ValueError(f"Line {line_number}: missing list field '{field}'")
            records.append(record)
    if not records:
        raise ValueError("No evaluation records found")
    return records


def evaluate(records: list[dict[str, Any]], k: int) -> dict[str, float | int]:
    recalls = []
    precisions = []
    mrrs = []
    ndcgs = []
    for record in records:
        relevant = {str(value) for value in record["relevant_documents"]}
        retrieved = [str(value) for value in record["retrieved_documents"]]
        recalls.append(recall_at_k(relevant, retrieved, k))
        precisions.append(precision_at_k(relevant, retrieved, k))
        mrrs.append(reciprocal_rank(relevant, retrieved))
        ndcgs.append(ndcg_at_k(relevant, retrieved, k))

    return {
        "examples": len(records),
        f"recall@{k}": round(mean(recalls), 6),
        f"precision@{k}": round(mean(precisions), 6),
        "mrr": round(mean(mrrs), 6),
        f"ndcg@{k}": round(mean(ndcgs), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSONL file containing retrieval predictions")
    parser.add_argument("--k", type=int, default=5, help="cutoff K (default: 5)")
    parser.add_argument("--output", type=Path, help="optional JSON output path")
    args = parser.parse_args()

    if args.k < 1:
        parser.error("--k must be >= 1")

    result = evaluate(load_records(args.input), args.k)
    payload = json.dumps(result, indent=2)
    print(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
