import pytest

from adapters.livekit_bridge import GraphBackedAssistant, create_assistant
from agent import AGENT_NAME
from graph.graph import greeting_text
from tools.weather import lookup_weather


@pytest.mark.asyncio
async def test_lookup_weather_direct() -> None:
    agent = create_assistant()
    reply = await agent.lookup_weather(None, "Paris")  # type: ignore[arg-type]
    assert "Paris" in reply
    assert "sunny" in reply.lower()


def test_weather_tool_module() -> None:
    reply = lookup_weather("London")
    assert "London" in reply


def test_agent_name_is_poc() -> None:
    assert AGENT_NAME == "v2v-poc-agent"


def test_greeting_from_graph() -> None:
    text = greeting_text()
    assert "LiveKit" in text
    assert len(text) > 10


def test_assistant_tracks_graph_state() -> None:
    agent = GraphBackedAssistant()
    greet = agent.greeting_message()
    assert agent.graph_state.get("should_greet") is False
    assert greet == agent.graph_state.get("last_agent_text")
    agent.note_user_text("Hello")
    assert agent.graph_state.get("last_user_text") == "Hello"
