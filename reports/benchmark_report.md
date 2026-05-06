# Benchmark Report: Single-Agent vs Multi-Agent

## Metrics Comparison

| Run | Latency (s) | Cost (USD) | Quality /10 | Notes |
|---|---:|---:|---:|---|
| single-agent | 13.89s | $0.00045 | 8.5 | citations=0/5 errors=0 route=[N/A] |
| multi-agent | 51.66s | $0.00181 | 8.5 | citations=5/5 errors=0 route=[researcher->analyst->writer->done] |

## Analysis

- **Latency**: Multi-agent is +37.77s (slower) than baseline.
- **Cost**: Multi-agent costs +$0.00136 (more) than baseline.
- **Quality**: Multi-agent scores +0.0 pts vs baseline (8.5 -> 8.5).

## Answer Excerpts

### single-agent

GraphRAG (Graph Retrieval-Augmented Generation) is an innovative framework that combines the strengths of graph-based data representation with retrieval-augmented generation techniques in natural language processing (NLP). This approach is particularly effective for tasks that require understanding complex relationships and structures within data, such as question answering, summarization, and dialogue systems. By leveraging graph structures, GraphRAG enhances the retrieval of relevant information, which is then used to generate coherent and contextually appropriate responses.

### Key Points:…

### multi-agent

# GraphRAG: A State-of-the-Art Framework for Graph Representation Learning

GraphRAG is an innovative framework that merges graph neural networks (GNNs) with attention mechanisms to enhance representation learning for graph-structured data. This approach not only improves the performance of various tasks such as node classification and link prediction but also addresses the complexities inherent in graph data. The integration of these technologies positions GraphRAG as a state-of-the-art solution in the field of graph representation learning.

## Key Features of GraphRAG

1. **Integration of G…


## Failure Modes & Mitigations

| Mode | Observation | Fix applied |
|---|---|---|
| Infinite loop | Agent could route indefinitely | `max_iterations` cap in SupervisorAgent |
| LLM timeout | API call hangs | `timeout=60` + exponential-backoff retry (3x) |
| Bad JSON from search | SearchClient parse error | Fallback `SourceDocument` returned |
| Missing notes | Analyst/Writer called without prior data | Guard clauses append to `state.errors` |

## Exit Ticket

### 1. Case nao nen dung multi-agent? Vi sao?

**Nen dung khi:**
- Nhiem vu co the chia thanh cac buoc doc lap ro rang (research -> analyze -> write)
- Moi buoc can cau hinh LLM khac nhau (temperature, system prompt chuyen biet)
- Can co kha nang debug tung buoc rieng biet
- Ket qua can co nguon trich dan (researcher lay nguon, writer dung nguon do)
- Workflow co the song song hoa mot phan (nhieu researcher chay cung luc)

**Vi du phu hop:** Research assistant, code review pipeline (lint -> test -> review), data pipeline (extract -> transform -> validate).

### 2. Case nao khong nen dung multi-agent? Vi sao?

**Khong nen dung khi:**
- Nhiem vu don gian, mot LLM call la du (QA chit-chat, classification, summarization ngan)
- Latency la uu tien hang dau: multi-agent cham hon 3-4x do nhieu round-trip LLM
- Chi phi la rang buoc cung: moi agent them 1 LLM call, tong cost tang tuyen tinh
- Chua co dang bai ro: neu chua biet agent nao can gi, tach ra se tao coupling phuc tap
- Team nho, it thoi gian: overhead de debug distributed state lon hon loi ich

**Nguyen tac nhanh:** Neu co the giai quyet bang 1 prompt tot, hay lam vay truoc. Chi them agent khi co measurable gain.
