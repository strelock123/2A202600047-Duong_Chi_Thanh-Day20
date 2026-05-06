"""Benchmark report rendering — markdown table + comparison analysis."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(
    metrics: list[BenchmarkMetrics],
    answers: dict[str, str] | None = None,
) -> str:
    """Render benchmark metrics to a rich markdown report.

    Args:
        metrics: List of BenchmarkMetrics from run_benchmark().
        answers: Optional dict of run_name → final_answer for qualitative comparison.
    """
    lines: list[str] = [
        "# Benchmark Report: Single-Agent vs Multi-Agent",
        "",
        "## Metrics Comparison",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality /10 | Notes |",
        "|---|---:|---:|---:|---|",
    ]

    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.5f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f}s | {cost} | {quality} | {item.notes} |"
        )

    # Qualitative comparison section
    if len(metrics) >= 2:
        lines += ["", "## Analysis", ""]
        baseline = metrics[0]
        multi = metrics[1]

        latency_delta = multi.latency_seconds - baseline.latency_seconds
        latency_sign = "+" if latency_delta >= 0 else ""
        lines.append(
            f"- **Latency**: Multi-agent is {latency_sign}{latency_delta:.2f}s "
            f"({'slower' if latency_delta > 0 else 'faster'}) than baseline."
        )

        if baseline.estimated_cost_usd and multi.estimated_cost_usd:
            cost_delta = multi.estimated_cost_usd - baseline.estimated_cost_usd
            cost_sign = "+" if cost_delta >= 0 else ""
            lines.append(
                f"- **Cost**: Multi-agent costs {cost_sign}${cost_delta:.5f} "
                f"({'more' if cost_delta > 0 else 'less'}) than baseline."
            )

        if baseline.quality_score is not None and multi.quality_score is not None:
            quality_delta = multi.quality_score - baseline.quality_score
            quality_sign = "+" if quality_delta >= 0 else ""
            lines.append(
                f"- **Quality**: Multi-agent scores {quality_sign}{quality_delta:.1f} pts "
                f"vs baseline ({baseline.quality_score:.1f} -> {multi.quality_score:.1f})."
            )

    # Answer excerpts
    if answers:
        lines += ["", "## Answer Excerpts", ""]
        for run_name, answer in answers.items():
            excerpt = (answer[:600] + "…") if len(answer) > 600 else answer
            lines += [f"### {run_name}", "", excerpt, ""]

    # Failure mode notes
    lines += [
        "",
        "## Failure Modes & Mitigations",
        "",
        "| Mode | Observation | Fix applied |",
        "|---|---|---|",
        "| Infinite loop | Agent could route indefinitely | `max_iterations` cap in SupervisorAgent |",
        "| LLM timeout | API call hangs | `timeout=60` + exponential-backoff retry (3×) |",
        "| Bad JSON from search | SearchClient parse error | Fallback `SourceDocument` returned |",
        "| Missing notes | Analyst/Writer called without prior data | Guard clauses append to `state.errors` |",
        "",
    ]

    return "\n".join(lines)
