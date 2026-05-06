"""Command-line entrypoint for the Multi-Agent Research Lab."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab CLI")
console = Console()

_BASELINE_SYSTEM = """You are an expert research assistant.
Answer the query comprehensively in 400-600 words.
Structure your response with:
1. A direct answer in the opening paragraph.
2. Key points as a bullet list.
3. A brief conclusion.
Be accurate, informative, and cite concepts clearly."""


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _baseline_runner(query: str) -> ResearchState:
    """Single-agent baseline: one LLM call, no tools, no pipeline."""
    llm = LLMClient(temperature=0.3)
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    resp = llm.complete(_BASELINE_SYSTEM, f"Research query: {query}")
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
    return state


def _multi_agent_runner(query: str) -> ResearchState:
    """Multi-agent pipeline: Supervisor → Researcher → Analyst → Writer."""
    state = ResearchState(request=ResearchQuery(query=query))
    return MultiAgentWorkflow().run(state)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the single-agent baseline and display the result."""
    _init()
    state, metrics = run_benchmark("single-agent-baseline", query, _baseline_runner)
    console.print(Panel.fit(state.final_answer or "(no answer)", title="Single-Agent Baseline"))
    console.print(
        f"Latency: {metrics.latency_seconds:.2f}s | "
        f"Cost: ${metrics.estimated_cost_usd or 0:.5f} | "
        f"Quality: {metrics.quality_score or 'N/A'}"
    )


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow and display the result."""
    _init()
    state, metrics = run_benchmark("multi-agent", query, _multi_agent_runner)
    console.print(Panel.fit(state.final_answer or "(no answer)", title="Multi-Agent Result"))
    console.print(f"Route: {' -> '.join(state.route_history)}")
    console.print(
        f"Latency: {metrics.latency_seconds:.2f}s | "
        f"Cost: ${metrics.estimated_cost_usd or 0:.5f} | "
        f"Quality: {metrics.quality_score or 'N/A'} | "
        f"Sources: {len(state.sources)}"
    )


@app.command()
def benchmark(
    query: Annotated[
        str,
        typer.Option("--query", "-q", help="Research query to benchmark"),
    ] = "Research GraphRAG state-of-the-art and write a 500-word summary",
) -> None:
    """Run both baseline and multi-agent, compare metrics, save report."""
    _init()

    console.print("[bold cyan]>> Running single-agent baseline...[/bold cyan]")
    baseline_state, baseline_metrics = run_benchmark(
        "single-agent", query, _baseline_runner
    )

    console.print("[bold cyan]>> Running multi-agent workflow...[/bold cyan]")
    multi_state, multi_metrics = run_benchmark("multi-agent", query, _multi_agent_runner)

    answers = {
        "single-agent": baseline_state.final_answer or "",
        "multi-agent": multi_state.final_answer or "",
    }
    report = render_markdown_report([baseline_metrics, multi_metrics], answers=answers)

    store = LocalArtifactStore()
    store.write_text("benchmark_report.md", report)

    # Print truncated summary to terminal (full report in file)
    for line in report.split("\n")[:30]:
        print(line)
    console.print("[green]Report saved to reports/benchmark_report.md[/green]")


if __name__ == "__main__":
    app()
