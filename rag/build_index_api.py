import os

import requests
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

from rag.config import CHROMA_DB_PATH

load_dotenv()

API_KEY = os.environ["API_KEY"]
API_URL = "http://127.0.0.1:8000/customers"
COLLECTION_NAME = "customers_api"


def build_document(customer: dict) -> str:
    """Format a customer record into the indexed document string."""
    return (
        f"Customer ID: {customer['customer_id']}\n"
        f"Name: {customer['first_name']} {customer['last_name']}\n"
        f"Age: {customer['age']}\n"
        f"Occupation: {customer['occupation']}\n"
        f"Annual Income: {customer['annual_income']}\n"
        f"Customer Segment: {customer['customer_segment']}\n"
        f"Preferred Product: {customer['preferred_product']}\n"
        f"Total Spent: {customer['total_spent']}\n"
        f"Loyalty Points: {customer['loyalty_points']}\n"
        f"Risk Score: {customer['risk_score']}"
    )


def main() -> None:
    try:
        # ------------------------------------------------------------------
        # 1. Fetch customer data from the FastAPI endpoint
        # ------------------------------------------------------------------
        print("Fetching customers from API...")
        resp = requests.get(
            API_URL,
            headers={"X-API-KEY": API_KEY},
            timeout=30,
        )
        resp.raise_for_status()
        customers: list[dict] = resp.json()
        print(f"Fetched {len(customers)} customers")

        # ------------------------------------------------------------------
        # 2. Build document strings and extract ids
        # ------------------------------------------------------------------
        documents = [build_document(c) for c in customers]
        ids = [str(c["customer_id"]) for c in customers]

        # ------------------------------------------------------------------
        # 3. Load the embedding model
        # ------------------------------------------------------------------
        print("Creating embeddings...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        embeddings = model.encode(documents, show_progress_bar=True).tolist()

        # ------------------------------------------------------------------
        # 4. Set up ChromaDB and (re)create the collection
        # ------------------------------------------------------------------
        print("Indexing...")
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )

        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        collection = client.get_or_create_collection(
            COLLECTION_NAME
        )

        # ------------------------------------------------------------------
        # 5. Add all documents to the collection
        # ------------------------------------------------------------------
        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
        )

        print("Index complete.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
