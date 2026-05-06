"""Analyst agent — turns research notes into structured analytical insights."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM = """You are a critical analyst. Given research notes on a topic, produce structured analysis
(300-400 words) with these sections:

## Key Claims
List the 3-5 most important findings from the research.

## Evidence Strength
For each claim, rate the evidence: Strong / Moderate / Weak, with a brief reason.

## Conflicting Views
Note any disagreements, gaps, or unresolved questions in the literature.

## Actionable Insights
What should the reader conclude or do based on this research?

Be objective, precise, and flag weak evidence clearly."""


class AnalystAgent(BaseAgent):
    """Extracts key claims, assesses evidence, and surfaces conflicts."""

    name = "analyst"

    def __init__(self) -> None:
        self._llm = LLMClient(temperature=0.1)

    def run(self, state: ResearchState) -> ResearchState:
        if not state.research_notes:
            state.errors.append("AnalystAgent: research_notes is empty — cannot analyse.")
            return state

        user = (
            f"Query: {state.request.query}\n\n"
            f"Research notes:\n{state.research_notes}\n\n"
            "Produce structured analysis."
        )

        resp = self._llm.complete(_SYSTEM, user)
        state.analysis_notes = resp.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=resp.content,
                metadata={
                    "cost_usd": resp.cost_usd,
                    "input_tokens": resp.input_tokens,
                    "output_tokens": resp.output_tokens,
                },
            )
        )
        state.add_trace_event("analyst.done", {"analysis_length": len(resp.content)})
        logger.info("Analyst: wrote %d chars of analysis.", len(resp.content))
        return state
