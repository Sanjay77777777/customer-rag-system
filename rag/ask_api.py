import os

import chromadb
from chromadb.config import Settings
import ollama
import psycopg2
from dotenv import load_dotenv

from rag.config import CHROMA_DB_PATH

load_dotenv()

# ------------------------------------------------------------------
# Database configuration (read from .env)
# ------------------------------------------------------------------
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "customerdb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))

COLLECTION_NAME = "customers_api"

# Keywords that trigger SQL routing
SQL_KEYWORDS = [
    "count",
    "how many",
    "highest",
    "lowest",
    "average",
    "sum",
    "top",
    "most",
    "least",
]


def classify_question(question: str) -> bool:
    """Return True if the question should be routed to SQL."""
    q = question.lower()
    return any(kw in q for kw in SQL_KEYWORDS)


def run_sql_query(question: str) -> str:
    """Route the question to a hard-coded SQL query and return the result."""
    q = question.lower()
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )
    try:
        cur = conn.cursor()

        if ("count" in q or "how many" in q) and "customer" in q:
            cur.execute("SELECT COUNT(*) FROM customers_rag_safe;")
            count = cur.fetchone()[0]
            return f"Total customers: {count}"

        if "highest" in q and "income" in q:
            cur.execute(
                "SELECT * FROM customers_rag_safe ORDER BY annual_income DESC LIMIT 1;"
            )
            row = cur.fetchone()
            return f"Highest annual income:\n{row}"

        if "lowest" in q and "income" in q:
            cur.execute(
                "SELECT * FROM customers_rag_safe ORDER BY annual_income ASC LIMIT 1;"
            )
            row = cur.fetchone()
            return f"Lowest annual income:\n{row}"

        if "average" in q and "income" in q:
            cur.execute("SELECT AVG(annual_income) FROM customers_rag_safe;")
            avg = round(cur.fetchone()[0], 2)
            return f"Average annual income: ${avg}"

        if ("top" in q or "most" in q) and "loyalty" in q:
            cur.execute(
                "SELECT * FROM customers_rag_safe ORDER BY loyalty_points DESC LIMIT 1;"
            )
            row = cur.fetchone()
            return f"Top loyalty points:\n{row}"

        return "I could not find that information in the customer database."
    finally:
        conn.close()


def main() -> None:
    try:
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection(COLLECTION_NAME)

        print("Customer RAG Assistant Ready")
        print("Source: PostgreSQL → FastAPI → ChromaDB")
        print("Type 'exit' to quit.")

        while True:
            try:
                question = input("\nAsk a question (or type exit): ")

                if question.lower() in ("exit", "quit"):
                    break

                # ------------------------------------------------------------------
                # Route: SQL for aggregations, else RAG
                # ------------------------------------------------------------------
                if classify_question(question):
                    print("[SQL MODE]")
                    answer = run_sql_query(question)
                    print(answer)
                    continue

                print("[RAG MODE]")
                results = collection.query(
                    query_texts=[question],
                    n_results=15,
                )

                context = "\n\n".join(results["documents"][0])
                print(f"Retrieved {len(results['documents'][0])} records for context")

                prompt = f"""You are a customer analytics assistant.

Use only the provided customer records.

Do not invent information.

If information is unavailable, say:

"I could not find that information in the customer database."

Context:
{context}

Question:
{question}

Answer:"""

                response = ollama.chat(
                    model="qwen2.5-coder:7b",
                    messages=[{"role": "user", "content": prompt}],
                )

                print(response["message"]["content"])

            except Exception as e:
                print(f"An error occurred during retrieval: {e}")

    except Exception as e:
        print(f"Failed to initialize: {e}")


if __name__ == "__main__":
    main()
