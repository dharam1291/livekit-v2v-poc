"""Bridge LiveKit Agents session I/O with LangGraph orchestration state."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from livekit.agents import Agent, RunContext, function_tool

from graph.graph import build_agent_graph, greeting_text
from graph.nodes import mark_agent_turn, mark_interrupted, mark_user_turn
from graph.prompts import TOOL_UNAVAILABLE_IN_V2V, system_instructions_for
from graph.state import AgentGraphState, initial_state
from tools.computer_use import (
    computer_use_enabled,
    computer_use_failure_message,
    run_computer_use,
)
from tools.weather import lookup_weather, weather_tool_failure_message

logger = logging.getLogger("agent.bridge")


class GraphBackedAssistant(Agent):
    """LiveKit Agent that keeps LangGraph session state in sync."""

    def __init__(
        self,
        *,
        language: str | None = "en",
        tools_enabled: bool = True,
    ) -> None:
        super().__init__(instructions=system_instructions_for(language))
        self._graph = build_agent_graph()
        self._state: AgentGraphState = initial_state()
        self._language = language or "en"
        self._tools_enabled = tools_enabled

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
        if not self._tools_enabled:
            msg = TOOL_UNAVAILABLE_IN_V2V
            self.note_agent_text(msg, tool_name="lookup_weather")
            return msg
        try:
            result = lookup_weather(location)
            self.note_agent_text(result, tool_name="lookup_weather")
            return result
        except Exception:
            logger.exception("Weather tool failed for %s", location)
            fallback = weather_tool_failure_message(location)
            self.note_agent_text(fallback, tool_name="lookup_weather")
            return fallback

    @function_tool
    async def computer_use(
        self,
        context: RunContext,
        conversation: str,
        url: str = "",
        command: str = "",
        action_type: str = "BROWSER_TASK",
    ) -> str:
        """Control the user's computer for browser or terminal actions via Machine Y.

        ALWAYS call this tool when the user wants the computer to DO something
        in a browser or terminal. Do not say you cannot type or search — this
        tool supports typing, searching, screenshots, and terminal commands.
        Do not ask the user to rephrase — extract the command and call the tool.

        Call computer_use for:
        - Browser: open Chrome/browser, open a website/link, go to Google/YouTube,
          type or search on a page (e.g. "search for Today's news"), take a screenshot
        - Terminal: open/run anything in the terminal/shell (e.g. pwd, ls, whoami)

        Do NOT call computer_use for weather or general Q&A with no computer action.

        Arguments:
        - conversation: full user goal in plain language (required). Keep the user's
          words, including the command name (pwd, ls, etc.).
        - command: for terminal tasks, the EXACT shell command only (e.g. "pwd").
          Always fill this when the user names a command.
        - url: https URL when known; else empty
        - action_type: TERMINAL_TASK for shell/terminal; BROWSER_TASK for browser

        After the tool returns, briefly say what happened (include command output
        if present). Never mention tool names.

        Args:
            conversation: Full computer goal from the user.
            url: Optional absolute URL; empty if unknown.
            command: Exact shell command for terminal tasks (e.g. pwd).
            action_type: BROWSER_TASK or TERMINAL_TASK.
        """
        del context
        if not self._tools_enabled:
            msg = TOOL_UNAVAILABLE_IN_V2V
            self.note_agent_text(msg, tool_name="computer_use")
            return msg
        if not computer_use_enabled():
            msg = (
                "Computer use is currently disabled. "
                "Set COMPUTER_USE_ENABLED=true to turn it on."
            )
            self.note_agent_text(msg, tool_name="computer_use")
            return msg
        kind = (action_type or "BROWSER_TASK").strip().upper()
        if (command or "").strip():
            kind = "TERMINAL_TASK"
        if kind not in {"BROWSER_TASK", "TERMINAL_TASK"}:
            kind = "BROWSER_TASK"
        try:
            result = await asyncio.to_thread(
                run_computer_use,
                conversation,
                url=url or None,
                command=command or None,
                action_type=kind,
            )
            self.note_agent_text(result, tool_name="computer_use")
            return result
        except Exception:
            logger.exception("Computer use tool failed")
            fallback = computer_use_failure_message()
            self.note_agent_text(fallback, tool_name="computer_use")
            return fallback


def create_assistant(
    *,
    language: str | None = "en",
    tools_enabled: bool = True,
) -> GraphBackedAssistant:
    return GraphBackedAssistant(language=language, tools_enabled=tools_enabled)
