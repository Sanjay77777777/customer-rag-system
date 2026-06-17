# Customer RAG API

Retrieval-Augmented Generation system for querying customer data using FastAPI, ChromaDB, Ollama, and React.

## Architecture

- **Backend**: FastAPI (port 8000)
- **Vector DB**: ChromaDB with `nomic-embed-text` embeddings via Ollama
- **LLM**: Ollama (`qwen2.5-coder:7b`)
- **SQL DB**: PostgreSQL (`customers_rag_safe` table)
- **Frontend**: React + Vite (dev) / nginx (prod)

## Quick Start

```bash
docker compose up
```

- Frontend: http://localhost:3000
- API: http://localhost:8000

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service status |
| GET | `/health` | Health check |
| GET | `/customers` | List customers (with optional filters) |
| GET | `/analytics` | Aggregated analytics |
| GET | `/analytics/products` | Product preference counts |
| GET | `/analytics/segments` | Segment distribution |
| GET | `/analytics/income` | Average income by segment |
| POST | `/reindex` | Rebuild ChromaDB index from PostgreSQL |
| POST | `/chat` | Ask questions (SQL for analytics, RAG for everything else) |

## Prerequisites

- Docker & Docker Compose
- PostgreSQL running on host (port 5432)
- Ollama running on host (port 11434) with models:
  - `qwen2.5-coder:7b`
  - `nomic-embed-text`

## Environment

Copy `.env` to project root with:

```
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
POSTGRES_DB=customerdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```
