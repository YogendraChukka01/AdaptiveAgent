from __future__ import annotations

from typing import Any

from app.models.state import AgentState


def step_counter(state: AgentState) -> dict[str, Any]:
    return {"step_count": state.step_count + 1}
