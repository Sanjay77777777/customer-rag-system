# Path where ChromaDB will store the vector index on disk
CHROMA_DB_PATH = "./chroma_db"

# Name of the ChromaDB collection that will hold customer embeddings
COLLECTION_NAME = "customers"

# Ollama model used to convert text into vector embeddings
EMBEDDING_MODEL = "nomic-embed-text"

# Ollama server host (use host.docker.internal when API runs in Docker)
OLLAMA_HOST = "http://host.docker.internal:11434"
