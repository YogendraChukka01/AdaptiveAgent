from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import require_api_key

router = APIRouter(prefix="/evaluate", tags=["evaluate"])


class EvalRequest(BaseModel):
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str | None = None


class EvalResponse(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    ragas_score: float
    judge_model: str
    error: str | None = None


@router.post("", response_model=EvalResponse)
async def evaluate_rag(
    request: EvalRequest,
    _auth: str = Depends(require_api_key),
):
    """Evaluate a RAG response using Ragas framework.

    Metrics:
    - faithfulness: Are claims in the answer supported by context?
    - answer_relevancy: Does the answer address the query?
    - context_precision: Are relevant chunks ranked highly? (needs ground_truth)
    - context_recall: Did retrieval find everything needed? (needs ground_truth)
    """
    from app.services.eval import ragas_evaluator

    result = await ragas_evaluator.aevaluate(
        question=request.question,
        answer=request.answer,
        contexts=request.contexts,
        ground_truth=request.ground_truth,
    )

    return EvalResponse(
        faithfulness=result.faithfulness,
        answer_relevancy=result.answer_relevancy,
        context_precision=result.context_precision,
        context_recall=result.context_recall,
        ragas_score=result.ragas_score,
        judge_model=result.judge_model,
        error=result.error,
    )
