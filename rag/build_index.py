import os
import re

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from rag.config import CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "data.txt")
SEPARATOR = "----------------------------------------"


def read_records(filepath: str) -> list[str]:
    """Read and split the data file into individual customer records."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    # Split on the separator and strip whitespace from each chunk
    records = [r.strip() for r in content.split(SEPARATOR)]
    # Discard any empty chunks
    return [r for r in records if r]


def extract_customer_id(record: str) -> str | None:
    """Extract the numeric customer ID from a record, e.g. 'Customer ID: 1001'."""
    match = re.search(r"Customer ID:\s*(\d+)", record)
    return match.group(1) if match else None


def main() -> None:
    try:
        # ------------------------------------------------------------------
        # 1. Load raw customer records from the data file
        # ------------------------------------------------------------------
        print("Loading data...")
        records = read_records(DATA_FILE)
        if not records:
            print("No records found in data file.")
            return

        # ------------------------------------------------------------------
        # 2. Load the embedding model
        # ------------------------------------------------------------------
        print("Creating embeddings...")
        model = SentenceTransformer(EMBEDDING_MODEL)
        embeddings = model.encode(records, show_progress_bar=True).tolist()

        # ------------------------------------------------------------------
        # 3. Set up ChromaDB persistent client
        # ------------------------------------------------------------------
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )

        # ------------------------------------------------------------------
        # 4. Drop the existing collection (if any) and recreate it
        # ------------------------------------------------------------------
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            # Collection did not exist – that is fine
            pass
        collection = client.get_or_create_collection(COLLECTION_NAME)

        # ------------------------------------------------------------------
        # 5. Build document strings and ids, then index everything
        # ------------------------------------------------------------------
        print("Indexing records...")
        ids: list[str] = []
        for record in records:
            cid = extract_customer_id(record)
            ids.append(cid if cid else f"__unknown__{len(ids)}")

        collection.add(
            documents=records,
            embeddings=embeddings,
            ids=ids,
        )

        print("Index complete.")

    except Exception as e:
        print(f"An error occurred during indexing: {e}")
        raise


if __name__ == "__main__":
    main()
