"""Researcher agent — searches for sources and distils them into notes."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

logger = logging.getLogger(__name__)

_SYSTEM = """You are a research specialist. Given a query and a set of search results,
write concise research notes (300-500 words) that:
1. Summarize the key findings from each source.
2. Note important facts, statistics, and direct quotes.
3. Highlight gaps or conflicting information across sources.
Use structured markdown with clearly labelled sections."""


class ResearcherAgent(BaseAgent):
    """Searches for sources and synthesises them into research notes."""

    name = "researcher"

    def __init__(self) -> None:
        self._search = SearchClient()
        self._llm = LLMClient(temperature=0.2)

    def run(self, state: ResearchState) -> ResearchState:
        query = state.request.query
        max_sources = state.request.max_sources

        # Gather sources
        sources = self._search.search(query, max_results=max_sources)
        state.sources = sources
        logger.info("Researcher: found %d sources.", len(sources))

        if not sources:
            state.errors.append("ResearcherAgent: no sources returned.")
            return state

        source_block = "\n\n".join(
            f"**[{i + 1}] {s.title}**\nURL: {s.url or 'N/A'}\n{s.snippet}"
            for i, s in enumerate(sources)
        )

        user = (
            f"Research query: {query}\n"
            f"Audience: {state.request.audience}\n\n"
            f"Search results:\n{source_block}\n\n"
            "Write comprehensive research notes."
        )

        resp = self._llm.complete(_SYSTEM, user)
        state.research_notes = resp.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=resp.content,
                metadata={
                    "sources_count": len(sources),
                    "cost_usd": resp.cost_usd,
                    "input_tokens": resp.input_tokens,
                    "output_tokens": resp.output_tokens,
                },
            )
        )
        state.add_trace_event("researcher.done", {"sources_count": len(sources)})
        logger.info("Researcher: wrote %d chars of notes.", len(resp.content))
        return state
