# ---------------------------------------------------------------------------
# CHROMA_DB CONFIGURATION
# ---------------------------------------------------------------------------

# CHROMA_DB_PATH
# Filesystem path where ChromaDB stores its persistent vector index on disk.
# This directory (chroma_db/) is gitignored and gets regenerated whenever
# POST /reindex is called. The path is relative to the working directory
# (/app inside the Docker container, project root when running locally).
CHROMA_DB_PATH = "./chroma_db"

# COLLECTION_NAME
# Internal name of the ChromaDB collection that holds customer embeddings.
# Note: the API endpoints (main.py) hardcode "customers_api" as the actual
# collection name. This constant is retained for potential future use by
# standalone scripts but is NOT the collection used by the running API.
COLLECTION_NAME = "customers"

# ---------------------------------------------------------------------------
# OLLAMA CONFIGURATION
# ---------------------------------------------------------------------------

# EMBEDDING_MODEL
# The Ollama model used to convert text into vector embeddings.
# nomic-embed-text is a lightweight embedding model (768 dimensions)
# that runs efficiently on consumer hardware. It is used both for
# indexing (POST /reindex) and querying (POST /chat).
EMBEDDING_MODEL = "nomic-embed-text"

# OLLAMA_HOST
# URL of the Ollama server. When the API runs inside a Docker container,
# host.docker.internal resolves to the host machine (Windows/macOS) where
# Ollama is installed and running on port 11434.
#
# For local development outside Docker, change this to:
#   "http://127.0.0.1:11434"
OLLAMA_HOST = "http://host.docker.internal:11434"
