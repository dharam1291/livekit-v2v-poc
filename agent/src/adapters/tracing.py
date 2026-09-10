"""Session timeline traces: JSONL + LiveKit data + Jaeger/OTLP spans."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adapters.otel_setup import get_tracer

logger = logging.getLogger("agent.tracing")

TRACE_DATA_TOPIC = "session.trace"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _attr_str(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


@dataclass
class SessionTracer:
    session_id: str
    enabled: bool = True
    trace_dir: str = "traces"
    room: Any | None = None
    turn_index: int | None = None
    _path: Path | None = field(default=None, init=False, repr=False)
    _sink_ok: bool = field(default=True, init=False, repr=False)
    _jaeger_ok: bool = field(default=True, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.enabled:
            return
        try:
            root = Path(self.trace_dir)
            root.mkdir(parents=True, exist_ok=True)
            safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.session_id)[
                :80
            ]
            self._path = root / f"{safe_id}.jsonl"
        except OSError as exc:
            self._sink_ok = False
            logger.warning("Trace sink unavailable: %s", exc)

    def set_room(self, room: Any) -> None:
        self.room = room

    def set_turn_index(self, turn_index: int | None) -> None:
        self.turn_index = turn_index

    def _emit_jaeger_span(self, event: str, attrs: dict[str, Any]) -> None:
        if not self._jaeger_ok:
            return
        tracer = get_tracer()
        if tracer is None:
            return
        try:
            with tracer.start_as_current_span(f"voice.{event}") as span:
                span.set_attribute("session.id", self.session_id)
                span.set_attribute("voice.event", event)
                if self.turn_index is not None:
                    span.set_attribute("voice.turn_index", int(self.turn_index))
                for key, value in attrs.items():
                    if value is None:
                        continue
                    span.set_attribute(f"voice.{key}", _attr_str(value))
        except Exception as exc:  # noqa: BLE001 — soft-fail Jaeger
            self._jaeger_ok = False
            logger.warning("Jaeger span export failed (continuing call): %s", exc)

    def emit(self, event: str, **attrs: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "session_id": self.session_id,
            "ts": _utc_now(),
            "event": event,
            "turn_index": self.turn_index,
            "attrs": {k: v for k, v in attrs.items() if v is not None},
            "t_mono": time.monotonic(),
        }
        if not self.enabled:
            return payload

        # Jaeger / OTLP (primary operator backend)
        self._emit_jaeger_span(event, payload["attrs"])

        line = json.dumps(payload, ensure_ascii=False)
        if self._sink_ok and self._path is not None:
            try:
                with self._path.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
            except OSError as exc:
                self._sink_ok = False
                logger.warning("Trace write failed: %s", exc)
                payload_err = {
                    **payload,
                    "event": "trace_sink_error",
                    "attrs": {"error": str(exc)},
                }
                logger.info("trace %s", json.dumps(payload_err, ensure_ascii=False))
        else:
            logger.info("trace %s", line)

        room = self.room
        if room is not None:
            try:
                import asyncio

                local = getattr(room, "local_participant", None)
                if local is not None:
                    data = line.encode("utf-8")

                    async def _publish() -> None:
                        await local.publish_data(
                            data,
                            reliable=True,
                            topic=TRACE_DATA_TOPIC,
                        )

                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(_publish())
                    except RuntimeError:
                        pass
            except Exception as exc:  # noqa: BLE001 — soft-fail UI feed
                logger.debug("Trace room publish skipped: %s", exc)

        return payload
