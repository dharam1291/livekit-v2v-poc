"""Unit tests for computer_use tool client."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tools.computer_use import run_computer_use


def _resp(
    *,
    status: str,
    result: str = "",
    error_code: str = "",
    error_message: str = "",
    data: bytes = b"",
):
    error = SimpleNamespace(code=error_code, message=error_message)
    observation = SimpleNamespace(data=data)
    resp = SimpleNamespace(
        status=status,
        result=result,
        request_id="r1",
        error=error,
        observation=observation,
    )

    def has_field(name: str) -> bool:
        if name == "error":
            return bool(error_code or error_message)
        if name == "observation":
            return bool(data)
        return False

    resp.HasField = has_field  # type: ignore[method-assign]
    return resp


def test_run_computer_use_success_with_screenshot():
    stub = MagicMock()
    stub.ComputerUse.return_value = _resp(
        status="SUCCESS",
        result="Opened Chrome and captured screenshot",
        data=b"png",
    )
    channel = MagicMock()
    with (
        patch("tools.computer_use.grpc.insecure_channel", return_value=channel),
        patch(
            "tools.computer_use.computer_use_pb2_grpc.ComputerUseServiceStub",
            return_value=stub,
        ),
    ):
        out = run_computer_use(
            "Open Google and take a screenshot",
            url="https://www.google.com",
            target="127.0.0.1:50051",
        )
    assert "screenshot" in out.lower()
    req = stub.ComputerUse.call_args.args[0]
    assert req.action_type == "BROWSER_TASK"
    assert req.context["url"] == "https://www.google.com"


def test_run_computer_use_needs_input():
    stub = MagicMock()
    stub.ComputerUse.return_value = _resp(
        status="NEEDS_USER_INPUT",
        error_code="AMBIGUOUS_OR_MISSING_INPUT",
        error_message="need a URL",
    )
    with (
        patch("tools.computer_use.grpc.insecure_channel", return_value=MagicMock()),
        patch(
            "tools.computer_use.computer_use_pb2_grpc.ComputerUseServiceStub",
            return_value=stub,
        ),
    ):
        out = run_computer_use("do something")
    assert "more information" in out.lower()


@pytest.mark.asyncio
async def test_computer_use_tool_on_assistant():
    from adapters.livekit_bridge import create_assistant

    agent = create_assistant()
    with patch(
        "adapters.livekit_bridge.run_computer_use",
        return_value="Task done on Machine Y.",
    ):
        reply = await agent.computer_use(
            None,  # type: ignore[arg-type]
            "Open Chrome",
            "https://example.com",
        )
    assert "Machine Y" in reply
