"""Bridge LiveKit Agents session I/O with LangGraph orchestration state."""

from __future__ import annotations

import logging
from typing import Any

from livekit.agents import Agent, RunContext, function_tool

from graph.graph import build_agent_graph, greeting_text
from graph.nodes import mark_agent_turn, mark_interrupted, mark_user_turn
from graph.prompts import SYSTEM_INSTRUCTIONS
from graph.state import AgentGraphState, initial_state
from tools.weather import lookup_weather, weather_tool_failure_message

logger = logging.getLogger("agent.bridge")


class GraphBackedAssistant(Agent):
    """LiveKit Agent that keeps LangGraph session state in sync."""

    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_INSTRUCTIONS)
        self._graph = build_agent_graph()
        self._state: AgentGraphState = initial_state()

    @property
    def graph_state(self) -> AgentGraphState:
        return self._state

    def apply_update(self, update: dict[str, Any]) -> None:
        messages = update.pop("messages", None)
        self._state.update(update)
        if messages:
            existing = list(self._state.get("messages") or [])
            existing.extend(messages)
            self._state["messages"] = existing

    def note_user_text(self, text: str) -> None:
        self.apply_update(mark_user_turn(self._state, text))

    def note_agent_text(self, text: str, *, tool_name: str | None = None) -> None:
        self.apply_update(mark_agent_turn(self._state, text, tool_name=tool_name))

    def note_interrupted(self) -> None:
        self.apply_update(mark_interrupted(self._state))

    def greeting_message(self) -> str:
        text = greeting_text(self._graph)
        self.apply_update(
            {
                "should_greet": False,
                "last_agent_text": text,
                "messages": [{"role": "assistant", "content": text}],
            }
        )
        return text

    @function_tool
    async def lookup_weather(self, context: RunContext, location: str) -> str:
        """Look up current weather for a location.

        Args:
            location: City or place name to look up weather for.
        """
        del context
        try:
            result = lookup_weather(location)
            self.note_agent_text(result, tool_name="lookup_weather")
            return result
        except Exception:
            logger.exception("Weather tool failed for %s", location)
            fallback = weather_tool_failure_message(location)
            self.note_agent_text(fallback, tool_name="lookup_weather")
            return fallback


def create_assistant() -> GraphBackedAssistant:
    return GraphBackedAssistant()
