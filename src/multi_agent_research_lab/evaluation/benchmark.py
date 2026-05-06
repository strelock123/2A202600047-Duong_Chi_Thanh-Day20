"""Benchmark runner — measures latency, cost, quality, and citation coverage."""

import logging
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)

Runner = Callable[[str], ResearchState]

_QUALITY_SYSTEM = """You are an evaluator scoring a research answer. Score it 0-10 based on:
- Relevance (answers the query directly): 0-4 pts
- Depth (covers key aspects thoroughly): 0-3 pts
- Clarity (well-structured, readable): 0-2 pts
- Citations (references sources): 0-1 pt

Reply with ONLY a single number (e.g. 7.5). No explanation."""


def _estimate_cost(state: ResearchState) -> float:
    """Sum cost_usd from all agent_results metadata."""
    total = 0.0
    for result in state.agent_results:
        cost = result.metadata.get("cost_usd")
        if isinstance(cost, (int, float)):
            total += float(cost)
    return total


def _score_quality(query: str, answer: str) -> float | None:
    """Ask the LLM to rate the answer quality on a 0-10 scale."""
    if not answer:
        return 0.0
    try:
        from multi_agent_research_lab.services.llm_client import LLMClient

        llm = LLMClient(temperature=0.0)
        resp = llm.complete(
            _QUALITY_SYSTEM,
            f"Query: {query}\n\nAnswer:\n{answer[:3000]}",  # cap to avoid huge prompts
        )
        score = float(resp.content.strip().split()[0])
        return round(max(0.0, min(10.0, score)), 1)
    except Exception as exc:
        logger.warning("Quality scoring failed: %s", exc)
        return None


def _citation_coverage(state: ResearchState) -> str:
    """Report found/requested sources ratio."""
    return f"{len(state.sources)}/{state.request.max_sources}"


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Run a workflow and return state + full benchmark metrics."""
    logger.info("Benchmark '%s' starting for query: %s", run_name, query[:60])
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    cost = _estimate_cost(state)
    quality = _score_quality(query, state.final_answer or "")
    citations = _citation_coverage(state)
    route_str = "->".join(state.route_history) if state.route_history else "N/A"

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=round(latency, 2),
        estimated_cost_usd=round(cost, 6),
        quality_score=quality,
        notes=f"citations={citations} errors={len(state.errors)} route=[{route_str}]",
    )
    logger.info(
        "Benchmark '%s' done: %.2fs $%.5f quality=%s",
        run_name,
        latency,
        cost,
        quality,
    )
    return state, metrics
