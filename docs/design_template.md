# Design Template

## Problem

Xây dựng một research assistant có thể nhận câu hỏi kỹ thuật dài, tìm kiếm thông tin từ nhiều nguồn, phân tích và tổng hợp câu trả lời cuối cùng có dẫn nguồn. Hệ thống phải hoạt động ổn định, không chạy vô hạn, và có benchmark so sánh với single-agent baseline.

## Why multi-agent?

Single-agent làm toàn bộ trong một lần gọi LLM sẽ có các vấn đề:
- Không thể tìm kiếm web (không có tool) → thiếu thông tin mới
- Prompt quá dài khi kết hợp search + analysis + writing → giảm chất lượng từng bước
- Khó debug khi output sai: không biết bước nào sai
- Mỗi nhiệm vụ cần temperature khác nhau (analyst cần thấp, writer cần cao hơn)

Multi-agent cho phép tách rõ trách nhiệm, dùng setting khác nhau cho từng agent, và trace được từng bước.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Quyết định agent tiếp theo dựa trên state | ResearchState | route_history cập nhật | Loop nếu không có stop condition → dùng max_iterations |
| Researcher | Tìm kiếm nguồn và viết research notes | query, max_sources | state.sources, state.research_notes | Search trả về rỗng → fallback SourceDocument; LLM timeout → retry 3x |
| Analyst | Phân tích research notes, đánh giá độ tin cậy | state.research_notes | state.analysis_notes | research_notes rỗng → ghi error, không crash |
| Writer | Tổng hợp final answer có dẫn nguồn | research_notes, analysis_notes, sources | state.final_answer | Thiếu notes → ghi error và return sớm |

## Shared state

| Field | Kiểu | Lý do cần |
|---|---|---|
| `request` | ResearchQuery | Truyền query và config (max_sources, audience) cho tất cả agents |
| `iteration` | int | Đếm vòng lặp để enforce max_iterations |
| `route_history` | list[str] | Supervisor đọc để biết trạng thái hiện tại; dùng để trace luồng |
| `sources` | list[SourceDocument] | Researcher populate; Writer dùng để trích dẫn |
| `research_notes` | str | Handoff từ Researcher sang Analyst; Supervisor kiểm tra để routing |
| `analysis_notes` | str | Handoff từ Analyst sang Writer; Supervisor kiểm tra để routing |
| `final_answer` | str | Output cuối cùng; Supervisor kiểm tra để dừng |
| `agent_results` | list[AgentResult] | Lưu cost/token của từng agent để tính tổng cost |
| `trace` | list[dict] | Timeline sự kiện để debug và explain trace |
| `errors` | list[str] | Accumulate lỗi; Supervisor dừng nếu >= 3 errors |

## Routing policy

```
START
  |
  v
[Supervisor] --- research_notes is None? --> [Researcher] --> [Supervisor]
             --- analysis_notes is None? --> [Analyst]   --> [Supervisor]
             --- final_answer is None?   --> [Writer]    --> [Supervisor]
             --- final_answer exists?    --> END
             --- iteration >= max_iter?  --> END (với error nếu chưa có answer)
             --- errors >= 3?            --> END
```

## Guardrails

- **Max iterations**: `MAX_ITERATIONS=6` (env var), kiểm tra trong `SupervisorAgent.run()` trước mọi routing
- **Timeout**: `timeout=60s` trong `LLMClient` (OpenAI SDK), `TIMEOUT_SECONDS=60` (env var)
- **Retry**: `LLMClient.complete()` retry 3 lần với exponential backoff (1s, 2s, 4s)
- **Fallback**: `SearchClient.search()` trả về 1 `SourceDocument` mặc định nếu JSON parse fail
- **Validation**: `AnalystAgent` và `WriterAgent` kiểm tra guard clause: nếu input notes rỗng thì append error vào `state.errors` và return sớm, không crash

## Benchmark plan

**Query dùng để test:**
1. "Research GraphRAG state-of-the-art and write a 500-word summary"
2. "What is GraphRAG and how does it improve RAG systems?"

**Metrics:**

| Metric | Cách đo | Expected outcome |
|---|---|---|
| Latency | wall-clock time (perf_counter) | Multi-agent chậm hơn ~3-4x do nhiều LLM calls |
| Cost | Sum token cost từ agent_results.metadata | Multi-agent đắt hơn ~3-4x |
| Quality | LLM scoring 0-10 (tự động) | Multi-agent >= single-agent vì có search context |
| Citation coverage | sources_found / max_sources | Multi-agent = 5/5; Baseline = 0/5 |
| Failure rate | errors trong state / total runs | 0 với guardrails đúng |

**Kết quả thực tế (từ benchmark_report.md):**
- Single-agent: 12-14s, ~$0.00045, quality 8.5, 0 citations
- Multi-agent: 46-52s, ~$0.00181, quality 8.5, 5/5 citations
- Trade-off: Multi-agent chậm hơn 4x và đắt hơn 4x nhưng có dẫn nguồn đầy đủ
