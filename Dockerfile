# ---------------------------------------------------------------------------
# BACKEND DOCKERFILE
# ---------------------------------------------------------------------------
# Stage 1: Build the FastAPI application image.
# Uses python:3.12-slim for a small footprint (no build tools, minimal libs).

# python:3.12-slim is the official lightweight Python image based on Debian.
# It includes Python 3.12 and pip but omits compilers and headers to keep
# the image small (~120 MB vs ~900 MB for the full bookworm image).
FROM python:3.12-slim

# Set the working directory inside the container.
# All subsequent COPY/CMD paths are relative to this.
WORKDIR /app

# Copy dependency files first (layer caching optimization).
# Docker caches each layer; if requirements haven't changed, this layer
# is reused from cache instead of re-running pip install.
COPY requirements-api.txt requirements-rag.txt .

# Install all Python dependencies.
# --no-cache-dir prevents pip from caching package files, saving ~50 MB.
# Two requirement files are used:
#   requirements-api.txt - light deps for basic API startup (FastAPI, psycopg2)
#   requirements-rag.txt - heavy deps for RAG (chromadb, ollama, sentence-transformers)
RUN pip install --no-cache-dir -r requirements-api.txt -r requirements-rag.txt

# Copy application source code.
# .dockerignore excludes .env, __pycache__, chroma_db/, frontend/, etc.
COPY api/ api/
COPY rag/ rag/

# Document the port the application listens on.
# This is metadata — actual port binding is done via docker-compose or -p flag.
EXPOSE 8000

# Default command runs uvicorn with the FastAPI app.
# uvicorn is an ASGI server that serves FastAPI applications.
# api.main:app means: from api.main module, import `app` (the FastAPI instance).
# --host 0.0.0.0 makes it accessible from outside the container.
# --port 8000 matches the EXPOSE directive.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
