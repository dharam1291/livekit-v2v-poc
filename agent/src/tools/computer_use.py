"""Computer-use tool — calls Machine Y ComputerUse gRPC service."""

from __future__ import annotations

import logging
import os
import uuid

import grpc

from tools.computer_use_grpc import computer_use_pb2, computer_use_pb2_grpc

logger = logging.getLogger("agent.tools.computer_use")


def _target() -> str:
    return (
        os.getenv("COMPUTER_USE_GRPC_TARGET")
        or os.getenv("COMPUTER_USE_GRPC_URL")
        or "127.0.0.1:50051"
    ).strip()


def _timeout_sec() -> float:
    raw = os.getenv("COMPUTER_USE_TIMEOUT_SEC", "180")
    try:
        return float(raw)
    except ValueError:
        return 180.0


def computer_use_enabled() -> bool:
    raw = (os.getenv("COMPUTER_USE_ENABLED") or "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def run_computer_use(
    conversation: str,
    *,
    url: str | None = None,
    command: str | None = None,
    action_type: str = "BROWSER_TASK",
    request_id: str | None = None,
    target: str | None = None,
    timeout_sec: float | None = None,
) -> str:
    """Invoke Machine Y and return a short spoken-friendly summary."""
    goal = (conversation or "").strip()
    if not goal and not (command or "").strip():
        return (
            "I need a clearer computer task description, "
            "for example open a website or run pwd in the terminal."
        )
    if not goal:
        goal = f"Run terminal command: {(command or '').strip()}"

    context: dict[str, str] = {}
    if url and url.strip():
        context["url"] = url.strip()
    if command and command.strip():
        context["command"] = command.strip()

    # Auto-select terminal when a shell command is provided
    kind = (action_type or "BROWSER_TASK").strip().upper()
    if context.get("command") and kind == "BROWSER_TASK":
        kind = "TERMINAL_TASK"

    addr = (target or _target()).strip()
    timeout = timeout_sec if timeout_sec is not None else _timeout_sec()
    rid = (request_id or "").strip() or str(uuid.uuid4())

    logger.info(
        "computer_use request target=%s action_type=%s request_id=%s has_url=%s has_command=%s",
        addr,
        kind,
        rid,
        "url" in context,
        "command" in context,
    )

    channel = grpc.insecure_channel(addr)
    try:
        stub = computer_use_pb2_grpc.ComputerUseServiceStub(channel)
        resp = stub.ComputerUse(
            computer_use_pb2.ComputerUseRequest(
                request_id=rid,
                action_type=kind or "BROWSER_TASK",
                conversation=goal,
                context=context,
            ),
            timeout=timeout,
        )
    except grpc.RpcError as exc:
        logger.exception("computer_use gRPC failed")
        return (
            "I could not reach the computer-use service right now. "
            f"Connection error: {exc.code().name}. "
            "Make sure Machine Y is running and COMPUTER_USE_GRPC_TARGET is correct."
        )
    finally:
        channel.close()

    status = (resp.status or "").upper()
    result = (resp.result or "").strip()
    err_msg = ""
    if resp.HasField("error") and (resp.error.message or resp.error.code):
        err_msg = (resp.error.message or resp.error.code or "").strip()

    has_shot = resp.HasField("observation") and bool(resp.observation.data)
    logger.info(
        "computer_use response status=%s request_id=%s has_screenshot=%s",
        status,
        resp.request_id,
        has_shot,
    )

    if status == "SUCCESS":
        base = result or "The computer task completed successfully."
        if has_shot:
            return f"{base} I also captured a screenshot on that machine."
        return base

    if status == "NEEDS_USER_INPUT":
        detail = err_msg or result or "more information is required"
        return f"The computer needs more information before continuing: {detail}"

    detail = err_msg or result or "unknown error"
    return f"The computer task failed: {detail}"


def computer_use_failure_message() -> str:
    return (
        "I could not complete that computer task right now. "
        "Please try again in a moment."
    )
