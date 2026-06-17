# Customer RAG System

A local AI-powered customer analytics platform that answers natural language questions about customer data using Retrieval-Augmented Generation (RAG).

Ask questions in plain English — SQL handles aggregations, RAG handles semantic search over customer records.

---

## Overview

Customer RAG System connects a React dashboard to a FastAPI backend that intelligently routes queries. Analytical questions (counts, averages, highest/lowest) go directly to PostgreSQL. Everything else — "find me engineers making over 80k", "who are my Platinum customers" — is answered via semantic search over ChromaDB with grounded generation from a local LLM.

All AI processing runs locally using Ollama and ChromaDB — no external API calls, no customer data leaves your machine.

---

## Features

### Hybrid Query Routing
- Automatic detection of analytical vs semantic questions
- SQL routing for aggregations (count, highest, lowest, average, top)
- RAG routing for everything else (occupations, segments, products, descriptive queries)
- Spelling normalization via `difflib` — "docter" → "doctor", "enginer" → "engineer"

### Vector Search
- Embedding generation via Ollama (`nomic-embed-text`)
- Persistent storage in ChromaDB
- Semantic similarity search over customer records
- 15 retrieved documents per query for rich context

### Customer Dashboard
- Realtime analytics cards (total customers, average income, segment counts)
- Recharts visualizations (segment pie, product bar, income by segment)
- Filterable customer table (by ID, segment, product)
- Reindex button to rebuild vector index from PostgreSQL

### Production Hardening
- Sanitized error responses (no stack traces or schema details leaked)
- ChromaDB telemetry disabled
- Configurable Ollama host for Docker networking
- CORS configured for frontend origins
- Docker Compose orchestration

---

## Architecture

```text
Browser (React + Vite / nginx)
         │
         ▼
    FastAPI Backend
         │
         ├── GET /customers, /analytics/*  ────► PostgreSQL
         │                                       (direct SQL queries)
         │
         └── POST /chat ──► classify_question()
                │
                ├── SQL keywords?  ──► PostgreSQL
                │     (count, highest,     (aggregations)
                │      lowest, average,
                │      top, most, least)
                │
                └── RAG route?      ──► ChromaDB (semantic search)
                                           │
                                           ▼
                                      Ollama Qwen2.5-Coder
                                      (grounded answer)
```

---

## Tech Stack

### Backend
- **FastAPI** — web framework
- **Python 3.12** — core language
- **Pydantic** — request/response validation
- **psycopg2** — PostgreSQL driver

### AI Components
- **Ollama** — local model runner
- **nomic-embed-text** — embeddings (768d)
- **qwen2.5-coder:7b** — answer generation

### Vector Database
- **ChromaDB** — persistent vector store

### Frontend
- **React 19** — UI framework
- **Vite** — dev server
- **Recharts** — charts library
- **Axios** — HTTP client
- **nginx** — production static server

---

## Project Structure

```text
├── docker-compose.yml           # Orchestration
├── Dockerfile                   # Backend container
├── requirements-api.txt         # API dependencies
├── requirements-rag.txt         # RAG dependencies
├── .env                         # Configuration (gitignored)
├── api/
│   ├── main.py                  # FastAPI entry point + all endpoints
│   ├── auth.py                  # API key auth (reserved for future use)
│   ├── database.py              # PostgreSQL connection
│   └── schemas.py               # Pydantic models
├── rag/
│   └── config.py                # ChromaDB & Ollama configuration
├── frontend/
│   ├── Dockerfile               # Multi-stage frontend container
│   ├── nginx.conf               # nginx proxy config
│   ├── vite.config.js           # Vite dev proxy
│   └── src/
│       ├── App.jsx              # Router setup
│       ├── pages/
│       │   ├── Dashboard.jsx    # Analytics + reindex
│       │   ├── Customers.jsx    # Filterable customer table
│       │   ├── Analytics.jsx    # Charts (Recharts)
│       │   └── Chat.jsx         # Q&A interface
│       ├── components/          # Shared UI components
│       └── services/api.js      # Axios client
└── chroma_db/                   # ChromaDB persistent data (gitignored)
```

---

## System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| **RAM** | 8 GB | 16 GB |
| **Disk Space** | 2 GB | 5 GB |
| **CPU** | x86_64, 4 cores | x86_64, 8 cores |
| **OS** | Windows 10+, Linux, macOS 12+ | — |
| **Docker** | 24+ | Latest |
| **Ollama** | Installed and running | Latest version |

*ChromaDB storage scales with the number of customer records indexed. PostgreSQL runs externally.*

---

## Installation

### Prerequisites

- [Docker](https://docker.com) & Docker Compose
- [Ollama](https://ollama.ai) (must be installed and running on the host)
- PostgreSQL instance accessible from Docker (`host.docker.internal`)

### Pull Ollama Models

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5-coder:7b
ollama list
```

### Configure Environment

Create `.env` in the project root:

```env
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
POSTGRES_DB=customerdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

### Start with Docker Compose

```bash
docker compose up
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

---

## Usage

### Dashboard

Browse analytics cards showing total customers, average income, and segment counts. Click **Reindex Vector Database** to rebuild the ChromaDB index from PostgreSQL.

### Customers

Filter customers by ID, segment (Silver/Gold/Platinum), or preferred product. Active filter count shown on the Clear button.

### Analytics

Three interactive Recharts visualizations:
- **Segment Distribution** — pie chart
- **Product Preferences** — bar chart
- **Average Income by Segment** — bar chart

### Chat

Ask natural language questions:

```
Who are my Platinum customers?
Show me engineers making over 80k
How many customers do I have?
Who has the highest income?
Find me lawyers in the Gold segment
What is the average income?
Docter by profession              ← spelling corrected automatically
```

Analytical queries route to SQL. Everything else routes to ChromaDB + Ollama.

### API Examples

```bash
# List customers (with optional filters)
curl "http://localhost:8000/customers?segment=Platinum"

# Get analytics
curl http://localhost:8000/analytics

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are my Platinum customers?"}'

# Reindex vector database
curl -X POST http://localhost:8000/reindex
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service status |
| `GET` | `/health` | Health check |
| `GET` | `/customers` | List customers with optional filters (`?customer_id=&segment=&product=`) |
| `GET` | `/customers/{id}` | Single customer by ID |
| `GET` | `/analytics` | Aggregated analytics (count, avg income, segment counts) |
| `GET` | `/analytics/products` | Product preference counts |
| `GET` | `/analytics/segments` | Segment distribution |
| `GET` | `/analytics/income` | Average income by segment |
| `POST` | `/reindex` | Rebuild ChromaDB index from PostgreSQL |
| `POST` | `/chat` | Ask a question (SQL for analytics, RAG for semantic search) |

### Chat Request Format

```json
{
  "question": "Show me engineers in the Gold segment"
}
```

### Chat Response Format

```json
{
  "answer": "Here are the Gold segment engineers: John Smith (ID: 1001), Priya Patel (ID: 1006)..."
}
```

### Error Codes

| Code | When |
|------|------|
| `404` | Customer ID not found |
| `500` | Internal server error (sanitized, no stack traces leaked) |

---

## Performance

| Metric | Value |
|--------|-------|
| Embedding dimensions | 768 |
| Retrieval backend | ChromaDB (cosine similarity) |
| Retrieved documents per query | 15 |
| Embedding model | nomic-embed-text |
| Answer generation | qwen2.5-coder:7b |
| SQL routing | Keyword-based (count, highest, lowest, etc.) |
| Spelling correction | difflib.get_close_matches (cutoff 0.8) |

---

## Project Status

**Status:** Stable Release

**Version:** `v2.0`

---

## Future Improvements

- Streaming chat responses
- Advanced filtering (date range, spending thresholds)
- Export customer data (CSV/Excel)
- Authentication via configurable API key
- Incremental reindexing
- Pagination for customer list
- Multi-language support
- Role-based access control

---

## License

MIT License

---

## Author

**R. Sanjay**

Customer RAG System — AI-powered customer analytics using Local RAG, ChromaDB, Ollama, FastAPI, and React.
