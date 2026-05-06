# Benchmark Report: Single-Agent vs Multi-Agent

## Metrics Comparison

| Run | Latency (s) | Cost (USD) | Quality /10 | Notes |
|---|---:|---:|---:|---|
| single-agent | 13.41s | $0.00041 | 8.5 | citations=0/5 errors=0 route=[N/A] |
| multi-agent | 41.95s | $0.00173 | 8.5 | citations=5/5 errors=0 route=[researcher->analyst->writer->done] |

## Analysis

- **Latency**: Multi-agent is +28.54s (slower) than baseline.
- **Cost**: Multi-agent costs +$0.00132 (more) than baseline.
- **Quality**: Multi-agent scores +0.0 pts vs baseline (8.5 -> 8.5).

## Answer Excerpts

### single-agent

GraphRAG (Graph-based Retrieval-Augmented Generation) is a state-of-the-art framework that integrates graph structures into the retrieval-augmented generation process, enhancing the capabilities of generative models by leveraging the relational information present in graph data. This approach has shown significant promise in various applications, particularly in natural language processing (NLP) tasks such as question answering, summarization, and dialogue systems. 

### Key Points:

- **Conceptual Foundation**: GraphRAG builds on the principles of retrieval-augmented generation, where a gener…

### multi-agent

# Summary of GraphRAG: State-of-the-Art in Retrieval-Augmented Generation

GraphRAG is an innovative model that integrates graph structures into retrieval-augmented generation (RAG) frameworks, significantly enhancing the coherence and accuracy of generated text. This model not only outperforms traditional RAG approaches but also holds the potential to revolutionize various applications in natural language processing (NLP), such as chatbots and search engines.

## Key Features of GraphRAG

### 1. Graph-Based Architecture
GraphRAG employs a graph-based architecture that leverages relational inf…


## Execution Trace (Multi-Agent)

| Step | Event | Payload |
|---:|---|---|
| 1 | `supervisor.route` | next=researcher, iteration=1 |
| 2 | `researcher.done` | sources_count=5 |
| 3 | `supervisor.route` | next=analyst, iteration=2 |
| 4 | `analyst.done` | analysis_length=3159 |
| 5 | `supervisor.route` | next=writer, iteration=3 |
| 6 | `writer.done` | answer_length=4215 |
| 7 | `supervisor.route` | next=done, iteration=4 |

## Agent Cost Breakdown (Multi-Agent)

| Agent | Input tokens | Output tokens | Cost (USD) |
|---|---:|---:|---:|
| researcher | 549 | 753 | $0.00053 |
| analyst | 902 | 554 | $0.00047 |
| writer | 1632 | 808 | $0.00073 |
| **Total** | | | **$0.00173** |

## Failure Modes & Mitigations

| Mode | Observation | Fix applied |
|---|---|---|
| Infinite loop | Agent could route indefinitely | `max_iterations` cap in SupervisorAgent |
| LLM timeout | API call hangs | `timeout=60` + exponential-backoff retry (3×) |
| Bad JSON from search | SearchClient parse error | Fallback `SourceDocument` returned |
| Missing notes | Analyst/Writer called without prior data | Guard clauses append to `state.errors` |
