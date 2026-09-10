"""OpenTelemetry setup for exporting spans to Jaeger (OTLP HTTP)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("agent.otel")

_PROVIDER_READY = False


def setup_jaeger_tracing(
    *,
    service_name: str = "livekit-v2v-agent",
    otlp_endpoint: str | None = None,
    enabled: bool = True,
) -> bool:
    """
    Configure a global TracerProvider that exports to Jaeger via OTLP HTTP.

    Soft-fails if OTEL packages or the endpoint setup fail — calls must continue.
    ``otlp_endpoint`` should be the full traces URL, e.g.
    ``http://localhost:4318/v1/traces``.
    """
    global _PROVIDER_READY
    if not enabled:
        return False
    if _PROVIDER_READY:
        return True

    endpoint = (otlp_endpoint or "http://localhost:4318/v1/traces").strip()
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        logger.warning("OpenTelemetry not available; Jaeger export disabled: %s", exc)
        return False

    try:
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.namespace": "livekit-v2v-poc",
            }
        )
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _PROVIDER_READY = True
        logger.info("Jaeger/OTLP tracing enabled endpoint=%s", endpoint)
        return True
    except Exception as exc:  # noqa: BLE001 — soft-fail
        logger.warning("Failed to configure Jaeger/OTLP tracing: %s", exc)
        return False


def get_tracer(name: str = "livekit.v2v.session") -> Any | None:
    if not _PROVIDER_READY:
        return None
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except Exception:  # noqa: BLE001
        return None
