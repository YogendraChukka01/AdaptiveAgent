from __future__ import annotations

import json
import urllib.request


class OpenAICompatibleEmbedder:
    """Embeddings via any OpenAI-compatible ``/embeddings`` API.

    Works with Ollama (``/v1/embeddings``), vLLM, Together,
    OpenAI, etc. No vendor SDK required.
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
    ) -> None:
        self._model = model
        self._api_key = api_key
        self._timeout = timeout
        url = base_url or "https://api.openai.com/v1/embeddings"
        if not url.rstrip("/").endswith("/embeddings"):
            url = url.rstrip("/") + "/embeddings"
        self._url = url

    def encode(self, texts: list[str]) -> list[list[float]]:
        body = json.dumps({"input": texts, "model": self._model}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key and self._api_key != "EMPTY":
            headers["Authorization"] = f"Bearer {self._api_key}"

        req = urllib.request.Request(self._url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        data = payload.get("data", [])
        data.sort(key=lambda d: d.get("index", 0))
        return [item["embedding"] for item in data]
