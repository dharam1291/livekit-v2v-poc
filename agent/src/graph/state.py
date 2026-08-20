"""LangGraph session state for voice turns."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AgentGraphState(TypedDict, total=False):
    """In-call orchestration state (see specs/001-livekit-v2v/data-model.md)."""

    messages: Annotated[list[Any], operator.add]
    last_user_text: str | None
    last_agent_text: str | None
    pending_tool: dict[str, Any] | None
    should_greet: bool
    interrupted: bool
    ended: bool


def initial_state() -> AgentGraphState:
    return {
        "messages": [],
        "last_user_text": None,
        "last_agent_text": None,
        "pending_tool": None,
        "should_greet": True,
        "interrupted": False,
        "ended": False,
    }
