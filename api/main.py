import difflib
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2.extras

os.environ["ANONYMIZED_TELEMETRY"] = "False"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("chromadb").setLevel(logging.WARNING)

from api.database import get_connection

from api.schemas import AnalyticsResponse, HealthResponse, ChatRequest
from rag.config import CHROMA_DB_PATH, OLLAMA_HOST

# ------------------------------------------------------------------
# Hybrid SQL + RAG shared logic
# ------------------------------------------------------------------
SQL_KEYWORDS = [
    "count", "how many", "highest", "lowest",
    "average", "sum", "top", "most", "least",
]


def classify_question(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in SQL_KEYWORDS)


def run_sql_query(question: str) -> str:
    q = question.lower()
    conn = get_connection()
    try:
        cur = conn.cursor()

        if ("count" in q or "how many" in q) and "customer" in q:
            cur.execute("SELECT COUNT(*) FROM customers_rag_safe;")
            return f"Total customers: {cur.fetchone()[0]}"

        if "highest" in q and "income" in q:
            cur.execute(
                "SELECT * FROM customers_rag_safe ORDER BY annual_income DESC LIMIT 1;"
            )
            return f"Highest annual income:\n{cur.fetchone()}"

        if "lowest" in q and "income" in q:
            cur.execute(
                "SELECT * FROM customers_rag_safe ORDER BY annual_income ASC LIMIT 1;"
            )
            return f"Lowest annual income:\n{cur.fetchone()}"

        if "average" in q and "income" in q:
            cur.execute("SELECT AVG(annual_income) FROM customers_rag_safe;")
            avg = round(cur.fetchone()[0], 2)
            return f"Average annual income: ${avg}"

        if ("top" in q or "most" in q) and "loyalty" in q:
            cur.execute(
                "SELECT * FROM customers_rag_safe ORDER BY loyalty_points DESC LIMIT 1;"
            )
            return f"Top loyalty points:\n{cur.fetchone()}"

        return "I could not find that information in the customer database."
    finally:
        conn.close()


VOCABULARY = {
    "engineer", "teacher", "doctor", "designer", "lawyer",
    "software", "developer", "accountant", "marketing", "manager",
    "business", "owner", "data", "analyst",
    "gold", "silver", "platinum",
    "laptop", "tablet", "smartphone", "phone", "monitor",
    "desktop", "pc", "headphones",
    "count", "many", "highest", "lowest",
    "average", "sum", "top", "most", "least",
}


def normalize_question(question: str) -> str:
    original = question
    words = question.lower().split()
    corrected = []
    for word in words:
        match = difflib.get_close_matches(word, VOCABULARY, n=1, cutoff=0.8)
        if match:
            corrected.append(match[0])
        else:
            corrected.append(word)
    result = " ".join(corrected)
    if result != original.lower():
        logger.info(f"Corrected query '{original}' -> '{result}'")
    if len(result.split()) == 1:
        result = f"customers matching {result}"
    return result


logger.info(f"Using Ollama host: {OLLAMA_HOST}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-KEY", "Content-Type"],
)


@app.get("/")
def root():
    """Public health-check endpoint."""
    return {"service": "Customer RAG API", "status": "running"}


@app.get("/health", response_model=HealthResponse)
def health():
    """Public endpoint returning service health status."""
    return HealthResponse(status="healthy")


@app.get("/customers")
def get_customers(
    customer_id: int = None,
    segment: str = None,
    product: str = None,
):
    """Return customer records with optional filtering (API key required)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = "SELECT * FROM customers_rag_safe"
        conditions = []
        params = []

        if customer_id is not None:
            conditions.append("customer_id = %s")
            params.append(customer_id)
        if segment:
            conditions.append("customer_segment = %s")
            params.append(segment)
        if product:
            conditions.append("preferred_product = %s")
            params.append(product)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY customer_id;"
        cur.execute(query, params)
        return cur.fetchall()
    except Exception as e:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


@app.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
):
    """Return a single customer by ID (API key required)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM customers_rag_safe WHERE customer_id = %s;",
            (customer_id,),
        )
        row = cur.fetchone()
        if row is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Customer not found")
        return row
    except Exception as e:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


@app.get(
    "/analytics",
    response_model=AnalyticsResponse,
)
def get_analytics():
    """Return aggregated customer analytics (API key required)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM customers_rag_safe;")
        total_customers = cur.fetchone()[0]

        cur.execute("SELECT AVG(annual_income) FROM customers_rag_safe;")
        average_income = round(cur.fetchone()[0], 2)

        cur.execute(
            "SELECT COUNT(*) FROM customers_rag_safe WHERE customer_segment = 'Platinum';"
        )
        platinum_customers = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM customers_rag_safe WHERE customer_segment = 'Gold';"
        )
        gold_customers = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM customers_rag_safe WHERE customer_segment = 'Silver';"
        )
        silver_customers = cur.fetchone()[0]

        return AnalyticsResponse(
            total_customers=total_customers,
            average_income=average_income,
            platinum_customers=platinum_customers,
            gold_customers=gold_customers,
            silver_customers=silver_customers,
        )
    except Exception:
        logger.exception("Analytics endpoint failed")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )
    finally:
        if conn:
            conn.close()


@app.get("/analytics/products")
def get_analytics_products():
    """Return product counts (API key required)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT preferred_product AS product, COUNT(*) AS count "
            "FROM customers_rag_safe "
            "GROUP BY preferred_product "
            "ORDER BY product;"
        )
        return cur.fetchall()
    except Exception as e:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


@app.get("/analytics/segments")
def get_analytics_segments():
    """Return customer count per segment (API key required)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT customer_segment AS segment, COUNT(*) AS count "
            "FROM customers_rag_safe "
            "GROUP BY customer_segment "
            "ORDER BY segment;"
        )
        return cur.fetchall()
    except Exception as e:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


@app.get("/analytics/income")
def get_analytics_income():
    """Return average income per segment (API key required)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT customer_segment AS segment, AVG(annual_income)::int AS avg_income "
            "FROM customers_rag_safe "
            "GROUP BY customer_segment "
            "ORDER BY segment;"
        )
        return cur.fetchall()
    except Exception as e:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


@app.post("/reindex")
def reindex():
    """Rebuild the ChromaDB index from PostgreSQL data."""
    logger.info("Reindex requested")
    conn = None
    try:
        # ------------------------------------------------------------------
        # 1. Fetch all customers from the database
        # ------------------------------------------------------------------
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM customers_rag_safe ORDER BY customer_id;")
        customers = cur.fetchall()
        logger.info("Fetched %d customers from PostgreSQL", len(customers))
        conn.close()
        conn = None

        # ------------------------------------------------------------------
        # 2. Build document strings
        # ------------------------------------------------------------------
        documents = []
        for c in customers:
            doc = (
                f"Customer ID: {c['customer_id']}\n"
                f"Name: {c['first_name']} {c['last_name']}\n"
                f"Age: {c['age']}\n"
                f"Occupation: {c['occupation']}\n"
                f"Annual Income: {c['annual_income']}\n"
                f"Customer Segment: {c['customer_segment']}\n"
                f"Preferred Product: {c['preferred_product']}\n"
                f"Total Spent: {c['total_spent']}\n"
                f"Loyalty Points: {c['loyalty_points']}\n"
                f"Risk Score: {c['risk_score']}"
            )
            documents.append(doc)

        ids = [str(c["customer_id"]) for c in customers]

        # ------------------------------------------------------------------
        # 3. Generate embeddings via Ollama
        # ------------------------------------------------------------------
        import ollama
        ollama_client = ollama.Client(host=OLLAMA_HOST)
        logger.info("Generating embeddings...")
        embeddings = []
        for doc in documents:
            resp = ollama_client.embeddings(model="nomic-embed-text", prompt=doc)
            embeddings.append(resp["embedding"])
        logger.info("Embeddings generated")

        # ------------------------------------------------------------------
        # 4. Rebuild the ChromaDB collection
        # ------------------------------------------------------------------
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )

        try:
            client.delete_collection("customers_api")
            logger.info("Deleted existing collection")
        except Exception:
            logger.info("No existing collection to delete")

        collection = client.get_or_create_collection("customers_api")

        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
        )
        logger.info("Indexed %d documents", len(customers))

        return {
            "status": "success",
            "indexed_customers": len(customers),
        }

    except Exception as e:
        logger.error("Reindex failed: %s", e)
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


@app.post("/chat")
def chat(
    body: ChatRequest,
):
    """Hybrid SQL + RAG chat endpoint."""
    try:
        question = normalize_question(body.question)

        if classify_question(question):
            answer = run_sql_query(question)
            if "could not find" not in answer:
                return {"answer": answer}

        # RAG mode
        import chromadb
        from chromadb.config import Settings
        import ollama
        ollama_client = ollama.Client(host=OLLAMA_HOST)
        chroma_client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        collection = chroma_client.get_collection("customers_api")

        query_emb = ollama_client.embeddings(
            model="nomic-embed-text", prompt=question
        )["embedding"]

        results = collection.query(
            query_embeddings=[query_emb],
            n_results=15,
        )

        logger.info(f"Question: {question}")
        if results.get("documents"):
            logger.info(f"Retrieved docs: {results['documents'][0][:3]}")

        context = "\n\n".join(results["documents"][0])

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

        response = ollama_client.chat(
            model="qwen2.5-coder:7b",
            messages=[{"role": "user", "content": prompt}],
        )

        return {"answer": response["message"]["content"]}

    except Exception as e:
        return {"error": "An internal error occurred"}
