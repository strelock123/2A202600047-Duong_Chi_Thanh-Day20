# Multi-Agent Research System

> Lab 20 — Duong Chi Thanh (2A202600047)

He thong nghien cuu da agent: **Supervisor → Researcher → Analyst → Writer**, co benchmark so sanh voi single-agent baseline.

---

## Kien truc

```
User Query
    |
    v
Supervisor Agent        <-- quyet dinh buoc tiep theo
    |
    |---> Researcher Agent  --> state.sources + state.research_notes
    |---> Analyst Agent     --> state.analysis_notes
    |---> Writer Agent      --> state.final_answer
    |
    v
Benchmark Report + Trace
```

| Agent | Nhiem vu |
|---|---|
| **Supervisor** | Routing: doc state, chon agent tiep theo, enforce max_iterations |
| **Researcher** | Tim kiem nguon, tong hop research notes |
| **Analyst** | Phan tich notes, danh gia do tin cay, neu diem mau thuan |
| **Writer** | Viet final answer co dan nguon |

---

## Cau truc thu muc

```
.
├── src/multi_agent_research_lab/
│   ├── agents/          # Supervisor, Researcher, Analyst, Writer
│   ├── core/            # Config, State, Schemas, Errors
│   ├── graph/           # LangGraph workflow
│   ├── services/        # LLM client (OpenAI), Search client (mock)
│   ├── evaluation/      # Benchmark runner + report renderer
│   ├── observability/   # Logging + tracing hooks
│   └── cli.py           # CLI entrypoint
├── configs/             # lab_default.yaml
├── docs/                # design_template.md, peer_review_rubric.md
├── reports/             # benchmark_report.md, trace_example.json
└── tests/               # Unit tests
```

---

## Cai dat

### 1. Tao moi truong ao

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Cai dependencies

```bash
pip install -e ".[dev]"
```

Neu gap loi mang, thu:

```bash
pip install --no-cache-dir openai langgraph langchain-core pydantic pydantic-settings typer rich python-dotenv PyYAML tenacity
pip install -e . --no-deps
```

### 3. Cau hinh API key

```bash
cp .env.example .env
```

Mo `.env` va dien:

```env
OPENAI_API_KEY=sk-...      # bat buoc
OPENAI_MODEL=gpt-4o-mini   # mac dinh
MAX_ITERATIONS=6           # gioi han vong lap
TIMEOUT_SECONDS=60         # timeout LLM
```

> Khong can Tavily hay LangSmith — he thong dung LLM-powered mock search.

---

## Su dung

### Chay single-agent baseline

```bash
python -m multi_agent_research_lab.cli baseline \
  --query "What is GraphRAG and how does it improve RAG systems?"
```

Output: cau tra loi truc tiep tu 1 LLM call + latency/cost/quality.

### Chay multi-agent workflow

```bash
python -m multi_agent_research_lab.cli multi-agent \
  --query "What is GraphRAG and how does it improve RAG systems?"
```

Output: ket qua sau khi qua 3 agents (Researcher → Analyst → Writer) + route history.

### Chay benchmark (khuyen dung)

```bash
python -m multi_agent_research_lab.cli benchmark \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Lenh nay se:
1. Chay single-agent baseline
2. Chay multi-agent workflow
3. Do latency, cost, quality, citation coverage
4. Luu `reports/benchmark_report.md` — bang so sanh day du
5. Luu `reports/trace_example.json` — trace tung buoc cua multi-agent

---

## Ket qua benchmark thuc te

| Run | Latency | Cost | Quality /10 | Citations |
|---|---:|---:|---:|---:|
| single-agent | ~14s | ~$0.00045 | 8.5 | 0/5 |
| multi-agent | ~50s | ~$0.00181 | 8.5 | 5/5 |

**Nhan xet:**
- Multi-agent cham hon ~4x va dat hon ~4x
- Chat luong tuong duong nhung multi-agent co day du trich dan nguon
- Single-agent phu hop khi can toc do; multi-agent phu hop khi can nguon trich dan

---

## Trace & Observability

Sau khi chay `benchmark`, xem trace tai:

- **`reports/trace_example.json`** — trace JSON day du (route, events, chi phi tung agent)
- **`reports/benchmark_report.md`** — bang Execution Trace + Agent Cost Breakdown

Vi du trace:

```
supervisor.route  --> researcher  (iteration 1)
researcher.done   --> sources_count=5
supervisor.route  --> analyst     (iteration 2)
analyst.done      --> analysis_length=3159
supervisor.route  --> writer      (iteration 3)
writer.done       --> answer_length=4215
supervisor.route  --> done        (iteration 4)
```

---

## Guardrails

| Bao ve | Co che |
|---|---|
| Infinite loop | `MAX_ITERATIONS=6` trong SupervisorAgent |
| LLM treo | `timeout=60s` + retry 3 lan voi exponential backoff |
| Search loi JSON | Fallback tra ve 1 SourceDocument mac dinh |
| Agent thieu input | Guard clause → ghi `state.errors`, khong crash |
| Qua nhieu loi | `errors >= 3` → supervisor dung lai |

---

## Chay tests

```bash
pytest tests/ -v
```

---

## Deliverables

| # | File | Mo ta |
|---|---|---|
| 1 | GitHub repo | https://github.com/strelock123/2A202600047-Duong_Chi_Thanh-Day20 |
| 2 | `reports/trace_example.json` | Execution trace day du |
| 3 | `reports/benchmark_report.md` | So sanh single vs multi-agent |
| 4 | `docs/design_template.md` | Thiet ke he thong, failure modes, benchmark plan |

---

## Exit Ticket

**1. Khi nao nen dung multi-agent?**

Khi nhiem vu co the chia thanh cac buoc doc lap ro rang, moi buoc can cau hinh LLM khac nhau, hoac ket qua can co trich dan nguon cu the. Vi du: research pipeline, code review, data processing.

**2. Khi nao khong nen dung multi-agent?**

Khi nhiem vu don gian (1 LLM call la du), hoac latency/cost la rang buoc chinh. Quy tac: neu co the giai quyet bang 1 prompt tot, hay lam vay truoc.
