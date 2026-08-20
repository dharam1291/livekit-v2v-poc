"""LangGraph nodes for greeting, reply bookkeeping, and interruption."""

from __future__ import annotations

from typing import Any

from graph.prompts import GREETING_FALLBACK_TEXT
from graph.state import AgentGraphState


def greeting_node(state: AgentGraphState) -> dict[str, Any]:
    """Emit greeting text without requiring a prior user utterance."""
    text = GREETING_FALLBACK_TEXT
    return {
        "should_greet": False,
        "last_agent_text": text,
        "messages": [{"role": "assistant", "content": text}],
    }


def mark_user_turn(state: AgentGraphState, text: str) -> dict[str, Any]:
    cleaned = (text or "").strip()
    return {
        "last_user_text": cleaned,
        "interrupted": False,
        "messages": [{"role": "user", "content": cleaned}],
    }


def mark_agent_turn(
    state: AgentGraphState,
    text: str,
    *,
    tool_name: str | None = None,
) -> dict[str, Any]:
    cleaned = (text or "").strip()
    update: dict[str, Any] = {
        "last_agent_text": cleaned,
        "messages": [{"role": "assistant", "content": cleaned}],
        "pending_tool": None,
    }
    if tool_name:
        update["pending_tool"] = {"tool_name": tool_name, "result_summary": cleaned}
    return update


def mark_interrupted(state: AgentGraphState) -> dict[str, Any]:
    return {"interrupted": True}


def mark_ended(state: AgentGraphState) -> dict[str, Any]:
    return {"ended": True, "should_greet": False}
