"""Compile the LangGraph orchestration graph for the POC agent."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from graph.nodes import greeting_node
from graph.state import AgentGraphState


def build_agent_graph(llm: Any | None = None) -> Any:
    """
    Build the LangGraph used for voice-session orchestration.

    Core POC path: greeting node + explicit state transitions tracked by the
    LiveKit bridge. When an ``llm`` is supplied, callers may extend this graph;
    the realtime LiveKit Agents pipeline remains the speech runtime.
    """
    del llm  # reserved for future ChatOpenAI-backed reply nodes
    graph = StateGraph(AgentGraphState)
    graph.add_node("greet", greeting_node)
    graph.add_edge(START, "greet")
    graph.add_edge("greet", END)
    return graph.compile()


def greeting_text(graph: Any | None = None) -> str:
    """Run the greeting node for session start."""
    compiled = graph or build_agent_graph()
    result = compiled.invoke({"should_greet": True, "messages": []})
    text = result.get("last_agent_text")
    if isinstance(text, str) and text.strip():
        return text
    return str(greeting_node({})["last_agent_text"])
