from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import get_llm


def reason_with_evidence(
    query: str,
    documents: list[dict],
) -> tuple[str, list[str]]:
    llm = get_llm(temperature=0.2, max_tokens=2048)

    context = "\n\n".join(
        f"[Source: {d.get('source', 'unknown')}]\n{d.get('content', '')}"
        for d in documents
    )

    messages = [
        SystemMessage(content=(
            "You are a safe, explainable AI assistant. Reason step-by-step using ONLY the provided evidence.\n"
            "If evidence is insufficient, say so. Never fabricate information.\n"
            "Format your response as:\n"
            "REASONING: <step-by-step chain of thought>\n"
            "ANSWER: <final answer>"
        )),
        HumanMessage(content=f"Query: {query}\n\nEvidence:\n{context}"),
    ]

    response = llm.invoke(messages)
    content = response.content

    reasoning_parts: list[str] = []
    answer = content

    if "REASONING:" in content and "ANSWER:" in content:
        parts = content.split("ANSWER:", 1)
        reasoning_text = parts[0].replace("REASONING:", "").strip()
        reasoning_parts = [r.strip() for r in reasoning_text.split("\n") if r.strip()]
        answer = parts[1].strip()
    else:
        reasoning_parts = [content[:200]]

    return answer, reasoning_parts
