from __future__ import annotations

from app.models.state import AgentState


def step_counter(state: AgentState) -> dict:
    return {"step_count": state.step_count + 1}
