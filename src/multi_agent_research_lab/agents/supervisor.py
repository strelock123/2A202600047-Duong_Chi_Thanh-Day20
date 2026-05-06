"""Supervisor / router agent — decides which worker runs next."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Routes the workflow through researcher → analyst → writer, then stops."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        settings = get_settings()

        # Hard stop: too many errors
        if len(state.errors) >= 3:
            logger.error("Supervisor: too many errors (%d), stopping.", len(state.errors))
            state.record_route("done")
            state.add_trace_event("supervisor.route", {"next": "done", "reason": "too_many_errors"})
            return state

        # Hard stop: iteration cap
        if state.iteration >= settings.max_iterations:
            logger.warning("Supervisor: max iterations (%d) reached.", settings.max_iterations)
            if not state.final_answer:
                state.errors.append("Stopped: max_iterations reached without a final answer.")
            state.record_route("done")
            state.add_trace_event("supervisor.route", {"next": "done", "reason": "max_iterations"})
            return state

        # Sequential routing policy:
        # 1. No research yet  → researcher
        # 2. No analysis yet  → analyst
        # 3. No answer yet    → writer
        # 4. Have answer      → done
        if not state.research_notes:
            next_route = "researcher"
        elif not state.analysis_notes:
            next_route = "analyst"
        elif not state.final_answer:
            next_route = "writer"
        else:
            next_route = "done"

        logger.info(
            "Supervisor: iteration=%d -> %s", state.iteration, next_route
        )
        state.record_route(next_route)
        state.add_trace_event(
            "supervisor.route",
            {"next": next_route, "iteration": state.iteration},
        )
        return state
