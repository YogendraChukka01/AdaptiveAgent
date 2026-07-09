from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import get_llm

SYSTEM_PROMPT = """You are a task planner for a safe RAG agent. Break the user's query into a sequential plan of steps.
Available actions:
- retrieve: search for relevant documents
- analyze: examine retrieved information
- verify: check evidence
- respond: generate final answer

Return a JSON array of strings, e.g. ["retrieve", "analyze", "respond"]
Keep plans to 3-5 steps maximum. Never include unsafe actions."""


def create_plan(query: str) -> list[str]:
    try:
        llm = get_llm(temperature=0.1, max_tokens=512)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Query: {query}"),
        ]
        response = llm.invoke(messages)

        try:
            plan = json.loads(response.content.strip())
            if isinstance(plan, list) and all(isinstance(s, str) for s in plan):
                return plan[:5]
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    except (ImportError, ModuleNotFoundError, RuntimeError, ValueError, TypeError):
        pass

    return ["retrieve", "analyze", "verify", "respond"]
