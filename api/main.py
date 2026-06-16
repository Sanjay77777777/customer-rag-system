import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import psycopg2.extras
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api.database import get_connection
from api.auth import verify_api_key
from api.schemas import AnalyticsResponse, HealthResponse, ChatRequest
from rag.config import CHROMA_DB_PATH

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
    api_key: str = Depends(verify_api_key),
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
    api_key: str = Depends(verify_api_key),
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
def get_analytics(
    api_key: str = Depends(verify_api_key),
):
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
    except Exception as e:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


@app.get("/analytics/products")
def get_analytics_products(
    api_key: str = Depends(verify_api_key),
):
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
def get_analytics_segments(
    api_key: str = Depends(verify_api_key),
):
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
def get_analytics_income(
    api_key: str = Depends(verify_api_key),
):
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
def reindex(
    api_key: str = Depends(verify_api_key),
):
    """Rebuild the ChromaDB index from PostgreSQL data (API key required)."""
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
        # 3. Generate embeddings
        # ------------------------------------------------------------------
        logger.info("Generating embeddings...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        embeddings = model.encode(documents, show_progress_bar=True).tolist()
        logger.info("Embeddings generated")

        # ------------------------------------------------------------------
        # 4. Rebuild the ChromaDB collection
        # ------------------------------------------------------------------
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
    api_key: str = Depends(verify_api_key),
):
    """Hybrid SQL + RAG chat endpoint (API key required)."""
    try:
        question = body.question

        if classify_question(question):
            answer = run_sql_query(question)
            return {"answer": answer}

        # RAG mode
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection("customers_api")

        results = collection.query(
            query_texts=[question],
            n_results=15,
        )

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

        response = ollama.chat(
            model="qwen2.5-coder:7b",
            messages=[{"role": "user", "content": prompt}],
        )

        return {"answer": response["message"]["content"]}

    except Exception as e:
        return {"error": "An internal error occurred"}
