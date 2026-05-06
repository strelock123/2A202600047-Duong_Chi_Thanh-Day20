"""Writer agent — synthesises research and analysis into a final answer."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM = """You are a technical writer producing a final research answer.
Write a clear, well-structured response (400-600 words) that:
1. Directly answers the research query in the opening paragraph.
2. Incorporates key findings from both the research and analysis notes.
3. Cites sources using numbered brackets [1], [2], etc.
4. Uses markdown headings and bullet lists for readability.
5. Ends with a concise conclusion.

Write for the stated audience. Be precise — avoid padding."""


class WriterAgent(BaseAgent):
    """Synthesises research notes + analysis into the final answer."""

    name = "writer"

    def __init__(self) -> None:
        self._llm = LLMClient(temperature=0.4)

    def run(self, state: ResearchState) -> ResearchState:
        if not state.research_notes:
            state.errors.append("WriterAgent: research_notes missing.")
            return state
        if not state.analysis_notes:
            state.errors.append("WriterAgent: analysis_notes missing.")
            return state

        source_list = "\n".join(
            f"[{i + 1}] {s.title} — {s.url or 'N/A'}"
            for i, s in enumerate(state.sources)
        )

        user = (
            f"Query: {state.request.query}\n"
            f"Audience: {state.request.audience}\n\n"
            f"Research notes:\n{state.research_notes}\n\n"
            f"Analysis:\n{state.analysis_notes}\n\n"
            f"Sources:\n{source_list}\n\n"
            "Write the final answer."
        )

        resp = self._llm.complete(_SYSTEM, user)
        state.final_answer = resp.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=resp.content,
                metadata={
                    "cost_usd": resp.cost_usd,
                    "input_tokens": resp.input_tokens,
                    "output_tokens": resp.output_tokens,
                },
            )
        )
        state.add_trace_event("writer.done", {"answer_length": len(resp.content)})
        logger.info("Writer: wrote %d chars of final answer.", len(resp.content))
        return state
