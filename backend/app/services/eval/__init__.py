from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class EvalResult(BaseModel):
    """Single evaluation result."""

    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    ragas_score: float = 0.0
    metric_details: dict[str, Any] = {}
    judge_model: str = ""
    error: str | None = None


class RagasEvaluator:
    """Ragas evaluation framework integration.

    Wraps the Ragas library to evaluate RAG pipeline outputs against
    four core metrics: faithfulness, answer_relevancy, context_precision,
    context_recall.

    When Ragas is not installed, falls back to the built-in heuristic
    judge in eval_node.
    """

    def __init__(self) -> None:
        self._ragas_available = False
        self._llm = None
        self._embeddings = None
        try:
            import ragas  # noqa: F401

            self._ragas_available = True
        except ImportError:
            logger.debug("ragas not installed; using heuristic evaluation")

    def _get_ragas_llm(self) -> Any:
        if self._llm is not None:
            return self._llm
        try:
            from ragas.llms import LangchainLLMWrapper

            from app.services.llm import get_llm

            base_llm = get_llm(temperature=0.0, max_tokens=512)
            self._llm = LangchainLLMWrapper(base_llm)
            return self._llm
        except Exception:
            logger.debug("Failed to initialize Ragas LLM")
            return None

    def _get_ragas_embeddings(self) -> Any:
        if self._embeddings is not None:
            return self._embeddings
        try:
            from ragas.embeddings import LangchainEmbeddingsWrapper

            from app.services.retrieval.embeddings.embedder import get_embedder

            base_embedder = get_embedder()

            class _Wrapper:
                def embed_documents(self, texts):
                    return base_embedder.encode(texts).tolist()

                def embed_query(self, text):
                    return base_embedder.encode([text])[0].tolist()

            self._embeddings = LangchainEmbeddingsWrapper(_Wrapper())
            return self._embeddings
        except Exception:
            logger.debug("Failed to initialize Ragas embeddings")
            return None

    def evaluate(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None = None,
    ) -> EvalResult:
        """Evaluate a RAG response using Ragas metrics.

        Args:
            question: The user's query.
            answer: The generated response.
            contexts: Retrieved context chunks.
            ground_truth: Optional reference answer for reference-based metrics.

        Returns:
            EvalResult with faithfulness, answer_relevancy, etc.
        """
        if not self._ragas_available:
            return EvalResult(error="ragas not installed")

        try:
            from ragas import EvaluationDataset, SingleTurnSample, evaluate
            from ragas.metrics import answer_relevancy, faithfulness

            sample = SingleTurnSample(
                user_input=question,
                retrieved_contexts=contexts,
                response=answer,
                reference=ground_truth,
            )
            dataset = EvaluationDataset(samples=[sample])

            metrics = [faithfulness, answer_relevancy]
            if ground_truth:
                from ragas.metrics import context_precision, context_recall

                metrics.extend([context_precision, context_recall])

            ragas_llm = self._get_ragas_llm()
            ragas_embeddings = self._get_ragas_embeddings()

            evaluate_kwargs: dict[str, Any] = {}
            if ragas_llm:
                evaluate_kwargs["llm"] = ragas_llm
            if ragas_embeddings:
                evaluate_kwargs["embeddings"] = ragas_embeddings

            result = evaluate(
                dataset,
                metrics=metrics,
                **evaluate_kwargs,
            )

            row = result.to_pandas().iloc[0]
            faith = float(row.get("faithfulness", 0.0) or 0.0)
            relevancy = float(row.get("answer_relevancy", 0.0) or 0.0)
            precision = float(row.get("context_precision", 0.0) or 0.0)
            recall = float(row.get("context_recall", 0.0) or 0.0)

            scored_metrics = [m for m in [faith, relevancy] if m > 0]
            if ground_truth:
                scored_metrics.extend([m for m in [precision, recall] if m > 0])
            ragas_score = sum(scored_metrics) / len(scored_metrics) if scored_metrics else 0.0

            return EvalResult(
                faithfulness=faith,
                answer_relevancy=relevancy,
                context_precision=precision,
                context_recall=recall,
                ragas_score=ragas_score,
                judge_model=settings.eval_judge_model or settings.llm_model,
            )
        except Exception as e:
            logger.debug("Ragas evaluation failed: %s", e)
            return EvalResult(error=str(e))

    async def aevaluate(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None = None,
    ) -> EvalResult:
        """Async variant of evaluate (runs sync in thread)."""
        import asyncio

        return await asyncio.to_thread(self.evaluate, question, answer, contexts, ground_truth)


ragas_evaluator = RagasEvaluator()
