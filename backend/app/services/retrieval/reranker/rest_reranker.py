from __future__ import annotations

import json
import urllib.request


class RestReranker:
    """Reranker via any Jina/Cohere/Voyage-shaped rerank API.

    Sends ``{"model", "query", "documents", "top_n"}`` and reads
    ``{"results": [{"index", "relevance_score"}]}``.
    """

    def __init__(
        self,
        model: str,
        api_base: str | None,
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        if not api_base:
            raise ValueError(
                "reranker_api_base must be set when reranker_provider='rest'"
            )
        self._model = model
        self._api_base = api_base
        self._api_key = api_key
        self._timeout = timeout

    def compute_score(self, pairs: list[list[str]]) -> list[float]:
        if not pairs:
            return []
        query = pairs[0][0]
        documents = [p[1] for p in pairs]

        body = json.dumps(
            {
                "model": self._model,
                "query": query,
                "documents": documents,
                "top_n": len(documents),
            }
        ).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        req = urllib.request.Request(
            self._api_base, data=body, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        results = payload.get("results", [])
        scores: list[float] = [0.0] * len(documents)
        for item in results:
            idx = item.get("index")
            if isinstance(idx, int) and 0 <= idx < len(scores):
                scores[idx] = float(item.get("relevance_score", item.get("score", 0.0)))
        return scores
