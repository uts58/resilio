# Cyber Resilience AI Agent

[![CI](https://github.com/uts58/resilio/actions/workflows/ci.yml/badge.svg)](https://github.com/uts58/resilio/actions/workflows/ci.yml)

An AI-powered cybersecurity advisor for small and mid-sized businesses, providing intelligent guidance on security controls, risk assessment, and budget planning.

---

## Overview

The agent answers cybersecurity questions by combining:

- **Security Guidance** — NIST and CIS control recommendations via semantic search
- **Risk Calculations** — SLE, ARO, ALE, ROSI, and more
- **Budget Planning** — IT budget estimation and safeguard value analysis

It exposes all tools as a **standalone MCP HTTP server**, making them available to any MCP-compatible client (Claude Desktop, CLI agents, etc.) in addition to the built-in Streamlit UI and CLI.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11+ |
| **UI** | Streamlit |
| **LLM Orchestration** | LangChain + LangGraph (`create_react_agent`) |
| **LLM Provider** | Groq (`llama-3.3-70b-versatile`) |
| **Tool Protocol** | MCP (streamable-HTTP server, port 8001) |
| **Embeddings** | HuggingFace TEI (`all-MiniLM-L6-v2`, OpenAI-compatible API, port 8002) |
| **Vector Store** | ChromaDB |
| **Observability** | Langfuse (self-hosted) — traces, spans, token counts |
| **Trace Storage** | ClickHouse (columnar) + PostgreSQL (metadata) + Redis (queue) |
| **Blob Storage** | MinIO (S3-compatible, backs Langfuse event uploads) |
| **Package Manager** | uv |

---

## Project Structure

```
resilio/
├── agent/
│   └── agent.py              # MCPAgent — LangGraph ReAct agent over MCP HTTP
├── mcp_server/
│   └── server.py             # MCP server — all tools, embeddings, and retrieval in one place
├── helper/
│   └── helper.py             # Output rendering and text sanitization
├── data/
│   ├── knowledge_base.jsonl  # Security knowledge base (JSONL format)
│   └── eval_dataset.jsonl    # 25 Q&A pairs with ground truth for eval
├── eval/
│   └── run_ragas.py          # RAGAS scoring harness (faithfulness, recall, relevancy)
├── main.py                   # Streamlit application entrypoint
├── cli.py                    # CLI entrypoint
├── mcp.json                  # MCP client config (Claude Desktop, etc.)
├── docker-compose.yml        # Full stack — ChromaDB, TEI, Langfuse, MinIO, MCP server, app
├── Dockerfile                # App container
└── pyproject.toml            # Dependencies (managed by uv)
```

---

## Prerequisites

- **Python** 3.11+
- **uv** — [install](https://docs.astral.sh/uv/getting-started/installation/)
- **Docker** — for running the full stack
- **Groq API key** — [get one](https://console.groq.com/)

### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional — defaults work for Docker Compose and local dev
CHROMA_HOST=localhost
CHROMA_PORT=8000
MCP_SERVER_URL=http://localhost:8001/mcp
TEI_URL=http://localhost:8002
TEI_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Langfuse — pre-seeded on first startup, UI at http://localhost:3000
# LANGFUSE_HOST is read by the Python SDK; Docker Compose injects
# http://langfuse-server:3000 internally for the app container automatically
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-resilio-local
LANGFUSE_SECRET_KEY=sk-lf-resilio-local
LANGFUSE_USER_EMAIL=admin@resilio.local
LANGFUSE_USER_PASSWORD=changeme123

# MinIO — S3-compatible blob storage for Langfuse event uploads
# Console at http://localhost:9091
LANGFUSE_S3_ACCESS_KEY=minio
LANGFUSE_S3_SECRET_KEY=miniosecret
```

---

## Setup

### Docker Compose

The stack is split into two compose files — core app and observability — so you can run them independently.

**Core only** (ChromaDB, TEI, MCP server, Streamlit):
```bash
docker compose up -d
```

**Full stack with Langfuse observability:**
```bash
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d
```

First run takes a few minutes while TEI downloads the embedding model.

| Service | URL | Credentials | Compose file |
|---------|-----|-------------|--------------|
| Streamlit UI | http://localhost:8501 | — | core |
| MCP server | http://localhost:8001/mcp | — | core |
| Langfuse UI | http://localhost:3000 | `admin@resilio.local` / `changeme123` | langfuse |
| MinIO Console | http://localhost:9091 | `minio` / `miniosecret` | langfuse |

The Langfuse project is pre-seeded with API keys matching the defaults in `.env.example`. If you override `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`, update the values in `.env` to match.

To tear down only the observability stack (preserving core app data):
```bash
docker compose -f docker-compose.langfuse.yml down
```

### Local (without Docker)

Langfuse tracing is optional when running locally — the agent skips it if `LANGFUSE_PUBLIC_KEY` or `LANGFUSE_SECRET_KEY` are absent from `.env`. To trace locally, run the full Docker Compose stack and point `LANGFUSE_HOST` at `http://localhost:3000`.

**1. Start ChromaDB and TEI:**
```bash
docker run -p 8000:8000 chromadb/chroma:1.4.4
docker run -p 8002:80 ghcr.io/huggingface/text-embeddings-inference:cpu-1.9.3 \
  --model-id sentence-transformers/all-MiniLM-L6-v2 --port 80
```

**2. Install dependencies:**
```bash
uv sync
```

**3. Start the MCP server:**
```bash
uv run python -m mcp_server
```

**4. Run the app** (in a separate terminal):
```bash
uv run streamlit run main.py
```

Or the CLI:
```bash
uv run python cli.py
```

---

## MCP Server

The tools run as a standalone HTTP server (streamable-HTTP transport, port 8001). Any MCP-compatible client can connect to it directly.

**Run locally:**
```bash
uv run python -m mcp_server
# → listening on http://localhost:8001/mcp
```

**Connect Claude Desktop** — add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "resilio-tools": {
      "url": "http://localhost:8001/mcp",
      "transport": "streamable-http"
    }
  }
}
```

> ChromaDB must be running before the MCP server starts.

---

## Available Tools

| Tool | Description |
|------|-------------|
| `retrieve_cyber_context` | Semantic search over NIST/CIS knowledge base |
| `calc_it_budget` | Estimate IT budget (~1.47% of revenue) |
| `calc_sle` | Single Loss Expectancy (Asset Value × Exposure Factor) |
| `calc_aro` | Annual Rate of Occurrence |
| `calc_ale` | Annualized Loss Expectancy (SLE × ARO) |
| `calc_rosi` | Return on Security Investment |
| `calc_risk` | Basic risk score (Threat × Vulnerability × Impact) |
| `calc_risk_reduction` | Risk reduction percentage after controls |
| `calc_safeguard_value` | Value of a security control (ALE before − after) |
| `calc_payback_period` | Investment payback in years |
| `calc_it_risk_score` | Normalized IT risk score (0–100) |

---

## Observability

Every agent run is traced end-to-end in Langfuse — LLM calls, tool invocations, token counts, and latency. Open the Langfuse UI at `http://localhost:3000` and navigate to **Traces** to inspect runs.

Tracing is gated on `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` being set in `.env`. If either is missing, the agent runs without tracing — no errors.

---

## Evaluation

A 25-question Q&A set lives at `data/eval_dataset.jsonl` — 15 knowledge, 3 application, and 7 calculator questions across NIST CSF 2.0, NIST SP 800-53, and CIS Controls v8.

The RAGAS harness at `eval/run_ragas.py` scores the knowledge/application questions on three metrics:

| Metric | What it measures |
|--------|------------------|
| `faithfulness` | Is the answer grounded in the retrieved contexts? |
| `context_recall` | Did retrieval surface the facts present in the ground-truth answer? |
| `answer_relevancy` | Does the answer actually address the question? |

Calculator questions are skipped — they're tool-use, not RAG.

**Run it:**
```bash
# ChromaDB + TEI must be running (core docker compose is enough)
docker compose up -d
uv sync --group eval
uv run python -m eval.run_ragas                  # uses Settings.prompt_version
uv run python -m eval.run_ragas --prompt-version v1
```

Per-question scores print to stdout and persist to `data/eval_results_<version>.json`.

> Uses Groq `llama-3.3-70b-versatile` as both answerer and LLM judge, and the project's TEI server for embeddings. `GROQ_API_KEY` must be set.

### Latest results

18 RAG questions, `llama-3.3-70b-versatile`, top-k = 5.

| Metric | Score |
|--------|------:|
| `faithfulness` | **0.974** |
| `context_recall` | **0.778** |
| `answer_relevancy` | 0.569 \* |

\* `answer_relevancy` is undercounted: RAGAS requests `n=3` LLM samples per question to score variance, but Groq's chat API only supports `n=1`. ~5 of 18 rows came back as `NaN` and were dropped from the mean. Real number is likely meaningfully higher — a future change should either swap the judge to an `n>1`-capable model or move to the newer `ragas.metrics.collections` API.

**Known weak spots**

- CIS Control 1, 2, and 3 lookups (`cis_001`–`cis_003`) returned `context_recall = 0` — the canonical "Control N: <name>" strings live inside table-of-contents chunks of the source PDF and aren't surfacing as the top hit. Knowledge-base quality issue, not a metric artifact.

### Prompt versioning

Both the agent's system prompt and the eval-time RAG prompt live in `prompts.py` as a versioned registry. The agent picks its active version from `Settings.prompt_version` (env: `PROMPT_VERSION`); the eval harness takes `--prompt-version v1`. Every Langfuse trace is tagged with `prompt_version` as metadata, so you can filter runs by version in the Langfuse UI to compare quality across prompt revisions.

To A/B a new prompt: add a `v2` entry to `AGENT_SYSTEM` and/or `EVAL_RAG` in `prompts.py`, then:

```bash
uv run python -m eval.run_ragas --prompt-version v1   # baseline
uv run python -m eval.run_ragas --prompt-version v2   # candidate
diff data/eval_results_v1.json data/eval_results_v2.json
```

Each run writes to `data/eval_results_<version>.json` so you keep both score sets side by side.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Could not connect to ChromaDB` | Make sure ChromaDB is running on port 8000 |
| `GROQ_API_KEY not set` | Check your `.env` file or export the variable in your shell |
| Slow first run | TEI downloads the embedding model on first start — subsequent starts use the cached volume |
| MCP server fails to start | ChromaDB and TEI must both be reachable before the MCP server starts |
| TEI stuck in healthcheck | First start downloads the model (~90 MB) — wait up to 2 minutes |
| Agent can't reach MCP server | Check `MCP_SERVER_URL` in `.env` — default is `http://localhost:8001/mcp` |
| Langfuse login fails | Wipe both Postgres and ClickHouse volumes and restart: `docker compose down && docker volume rm resilio_langfuse_db resilio_langfuse_clickhouse && docker compose up -d` |
| No traces in Langfuse | Verify `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` in `.env` match **Settings → API Keys** in the Langfuse UI |

---

## Security Notes

- Never commit API keys — keep `.env` in `.gitignore`
- Rotate `GROQ_API_KEY` regularly
- The MCP server listens on port 8001 — restrict access if deploying beyond localhost
- Default Langfuse secrets (`NEXTAUTH_SECRET`, `SALT`, `ENCRYPTION_KEY`) in `.env.example` are placeholders — generate real values before exposing Langfuse beyond localhost