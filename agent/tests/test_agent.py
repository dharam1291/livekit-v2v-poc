import pytest

from adapters.config import AgentConfig
from adapters.eou import build_turn_handling
from adapters.livekit_bridge import GraphBackedAssistant, create_assistant
from adapters.mic_gate import apply_user_mic_muted
from adapters.speech_llm import SpeachesAudioChunkedStream, SpeachesTTS, build_tts
from agent import AGENT_NAME
from graph.graph import greeting_text
from tools.weather import lookup_weather


class _FakeInput:
    def __init__(self) -> None:
        self.audio_enabled = True

    def set_audio_enabled(self, enabled: bool) -> None:
        self.audio_enabled = enabled


class _FakeSession:
    def __init__(self) -> None:
        self.input = _FakeInput()
        self.cleared = 0

    def clear_user_turn(self) -> None:
        self.cleared += 1


def test_apply_user_mic_muted_pauses_input_and_clears_turn() -> None:
    session = _FakeSession()
    apply_user_mic_muted(session, muted=True)  # type: ignore[arg-type]
    assert session.input.audio_enabled is False
    assert session.cleared == 1
    apply_user_mic_muted(session, muted=False)  # type: ignore[arg-type]
    assert session.input.audio_enabled is True
    assert session.cleared == 1


def _sample_config(**overrides: object) -> AgentConfig:
    base = {
        "agent_name": "v2v-poc-agent",
        "llm_provider": "openai",
        "openai_model": "gpt-4o-mini",
        "openai_api_key": "test-key",
        "openai_base_url": None,
        "azure_endpoint": None,
        "azure_deployment": None,
        "openai_api_version": None,
        "speaches_base_url": "http://localhost:8000/v1",
        "whisper_model": "Systran/faster-whisper-small",
        "kokoro_model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
        "kokoro_voice": "af_heart",
    }
    base.update(overrides)
    return AgentConfig(**base)  # type: ignore[arg-type]


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


@pytest.mark.asyncio
async def test_build_tts_uses_speaches_binary_stream() -> None:
    """Speaches returns raw audio; LiveKit SSE path would push zero frames."""
    tts = build_tts(_sample_config())
    assert isinstance(tts, SpeachesTTS)
    stream = tts.synthesize("Hello from the POC.")
    assert isinstance(stream, SpeachesAudioChunkedStream)


def test_turn_handling_uses_local_vad() -> None:
    th = build_turn_handling(_sample_config())
    assert th["turn_detection"] == "vad"
    assert th["interruption"]["mode"] == "vad"
    assert "min_delay" in th["endpointing"]
