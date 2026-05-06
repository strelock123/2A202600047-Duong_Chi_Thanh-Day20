"""LangGraph multi-agent workflow — Supervisor → Researcher → Analyst → Writer."""

import logging
from typing import Any

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)


def _to_dict(state: ResearchState) -> dict[str, Any]:
    return state.model_dump()


def _from_dict(d: dict[str, Any]) -> ResearchState:
    return ResearchState.model_validate(d)


class MultiAgentWorkflow:
    """Builds and executes the LangGraph multi-agent research pipeline."""

    def build(self):
        """Create and compile the LangGraph StateGraph.

        Graph topology:
            supervisor ──(conditional)──> researcher ─┐
                       ──(conditional)──> analyst    ─┤─> supervisor (loop)
                       ──(conditional)──> writer     ─┘
                       ──(done)────────> END
        """
        from langgraph.graph import END, StateGraph

        supervisor = SupervisorAgent()
        researcher = ResearcherAgent()
        analyst = AnalystAgent()
        writer = WriterAgent()

        def _safe_run(agent, state_dict: dict) -> dict:
            try:
                return _to_dict(agent.run(_from_dict(state_dict)))
            except Exception as exc:
                logger.error("Agent %s raised: %s", agent.name, exc)
                s = _from_dict(state_dict)
                s.errors.append(f"{agent.name}: {exc}")
                return _to_dict(s)

        def supervisor_node(state: dict) -> dict:
            return _safe_run(supervisor, state)

        def researcher_node(state: dict) -> dict:
            return _safe_run(researcher, state)

        def analyst_node(state: dict) -> dict:
            return _safe_run(analyst, state)

        def writer_node(state: dict) -> dict:
            return _safe_run(writer, state)

        def route(state: dict) -> str:
            history: list[str] = state.get("route_history", [])
            decision = history[-1] if history else "done"
            logger.debug("LangGraph routing → %s", decision)
            return decision

        builder: StateGraph = StateGraph(dict)
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("researcher", researcher_node)
        builder.add_node("analyst", analyst_node)
        builder.add_node("writer", writer_node)

        builder.set_entry_point("supervisor")
        builder.add_conditional_edges(
            "supervisor",
            route,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END,
            },
        )
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "supervisor")

        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Compile and invoke the graph, returning the final ResearchState."""
        graph = self.build()
        result: dict[str, Any] = graph.invoke(_to_dict(state))
        return _from_dict(result)
