# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
# difflib is part of Python's standard library.
# It provides tools for comparing sequences, specifically get_close_matches
# which we use to correct minor spelling mistakes in user queries.
import difflib

# logging is a built-in Python module for emitting log messages.
# We use it to record server activity, errors, and debug information
# (e.g. question corrections, ChromaDB retrieval data).
import logging

# os is a built-in module for interacting with the operating system.
# We use it here to set an environment variable that disables ChromaDB
# telemetry before the library is imported.
import os

# FastAPI is a modern async web framework for building APIs in Python.
# FastAPI     - the main application class we instantiate
# HTTPException - lets us return structured HTTP error responses
from fastapi import FastAPI, HTTPException

# CORSMiddleware handles Cross-Origin Resource Sharing headers.
# Without it, a web browser at localhost:5173 would be blocked from
# making requests to our API at localhost:8000.
from fastapi.middleware.cors import CORSMiddleware

# psycopg2 is the PostgreSQL adapter for Python.
# extras provides RealDictCursor, which returns rows as dictionaries
# (keyed by column name) instead of plain tuples.
import psycopg2.extras

# ---------------------------------------------------------------------------
# CHROMADB TELEMETRY SUPPRESSION
# ---------------------------------------------------------------------------
# ChromaDB (the vector database) sends anonymous telemetry to PostHog by
# default. This environment variable tells it not to collect or send any
# telemetry data. We set it BEFORE any chromadb import so the library
# picks it up at initialization time.
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------
# basicConfig configures the root logger. Here we set it to INFO level,
# which means all INFO, WARNING, ERROR, and CRITICAL messages will appear.
logging.basicConfig(level=logging.INFO)

# __name__ evaluates to "api.main" when the module is run as part of the
# api package. This gives each module a unique logger name so we can tell
# which part of the code produced each log line.
logger = logging.getLogger(__name__)

# ChromaDB uses its own logger internally. We raise its threshold to
# WARNING so that its informational messages (telemetry errors, etc.) are
# suppressed from the console output.
logging.getLogger("chromadb").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# INTERNAL MODULE IMPORTS
# ---------------------------------------------------------------------------
# get_connection() is defined in api/database.py.
# It creates a new psycopg2 connection to PostgreSQL using credentials
# from the .env file (POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, etc.).
from api.database import get_connection

# Pydantic models that define the shape of request/response data.
# AnalyticsResponse - returned by GET /analytics
# HealthResponse    - returned by GET /health
# ChatRequest       - validated body for POST /chat
from api.schemas import AnalyticsResponse, HealthResponse, ChatRequest

# Configuration constants from rag/config.py:
# CHROMA_DB_PATH - filesystem path where ChromaDB stores vectors ("/chroma_db")
# OLLAMA_HOST    - URL of the Ollama server ("http://host.docker.internal:11434")
from rag.config import CHROMA_DB_PATH, OLLAMA_HOST

# ---------------------------------------------------------------------------
# SQL KEYWORD ROUTING
# ---------------------------------------------------------------------------
# These are the keywords that trigger direct SQL query execution instead of
# RAG-based retrieval. If a user's question contains any of these, we try
# to answer it from PostgreSQL directly.
SQL_KEYWORDS = [
    "count", "how many", "highest", "lowest",
    "average", "sum", "top", "most", "least",
]


def classify_question(question: str) -> bool:
    """Determine whether the question should be routed to SQL.

    Checks if any of the SQL_KEYWORDS appear anywhere in the question text.
    Returns True if a keyword is found (SQL route), False otherwise (RAG route).

    Example:
        "how many customers" -> True (contains "how many")
        "who are my lawyers" -> False (no keyword match)
    """
    q = question.lower()
    return any(kw in q for kw in SQL_KEYWORDS)


def run_sql_query(question: str) -> str:
    """Execute a hard-coded SQL query based on keyword patterns in the question.

    Each if-block checks for a specific combination of keywords and runs a
    corresponding SQL query. If no pattern matches, returns a fallback string
    indicating the question could not be answered from the database.

    The caller (POST /chat) checks for the fallback string and falls through
    to RAG if it sees it.

    Returns:
        A human-readable string answer.
    """
    q = question.lower()
    conn = get_connection()
    try:
        cur = conn.cursor()

        # --- "count / how many customers" ---
        # SELECT COUNT(*) gives total number of rows in the table.
        if ("count" in q or "how many" in q) and "customer" in q:
            cur.execute("SELECT COUNT(*) FROM customers_rag_safe;")
            return f"Total customers: {cur.fetchone()[0]}"

        # --- "highest income" ---
        # ORDER BY annual_income DESC LIMIT 1 returns the row with the
        # maximum annual income.
        if "highest" in q and "income" in q:
            cur.execute(
                "SELECT * FROM customers_rag_safe ORDER BY annual_income DESC LIMIT 1;"
            )
            return f"Highest annual income:\n{cur.fetchone()}"

        # --- "lowest income" ---
        # ORDER BY annual_income ASC LIMIT 1 returns the row with the
        # minimum annual income.
        if "lowest" in q and "income" in q:
            cur.execute(
                "SELECT * FROM customers_rag_safe ORDER BY annual_income ASC LIMIT 1;"
            )
            return f"Lowest annual income:\n{cur.fetchone()}"

        # --- "average income" ---
        # AVG() aggregates all rows and returns the mean annual_income.
        if "average" in q and "income" in q:
            cur.execute("SELECT AVG(annual_income) FROM customers_rag_safe;")
            avg = round(cur.fetchone()[0], 2)
            return f"Average annual income: ${avg}"

        # --- "top / most loyalty" ---
        # ORDER BY loyalty_points DESC LIMIT 1 returns the customer with
        # the highest loyalty points.
        if ("top" in q or "most" in q) and "loyalty" in q:
            cur.execute(
                "SELECT * FROM customers_rag_safe ORDER BY loyalty_points DESC LIMIT 1;"
            )
            return f"Top loyalty points:\n{cur.fetchone()}"

        # --- No pattern matched ---
        # This fallback tells the caller to try RAG instead.
        return "I could not find that information in the customer database."
    finally:
        # Ensure the database connection is always closed, even if an
        # exception occurs inside the try block.
        conn.close()


# ---------------------------------------------------------------------------
# SPELLING CORRECTION VOCABULARY
# ---------------------------------------------------------------------------
# This set contains domain-specific words that users commonly misspell.
# difflib.get_close_matches() compares each word of the user's question
# against this vocabulary and replaces it with the closest match if the
# similarity is above the cutoff threshold.
#
# The vocabulary is grouped by category:
#   - Occupations       (doctor, engineer, lawyer, accountant, etc.)
#   - Customer Segments (gold, silver, platinum)
#   - Preferred Products(laptop, tablet, smartphone, monitor, etc.)
#   - SQL Keywords      (count, many, highest, lowest, average, etc.)
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
    """Correct minor spelling mistakes and wrap single-word queries.

    Steps:
    1. Split the question into individual words.
    2. For each word, try to find a close match in VOCABULARY.
       difflib.get_close_matches() returns the best match if similarity >= 0.8.
    3. If corrected text differs from the original, log the correction.
    4. If the result is a single word (e.g. "doctor"), wrap it into
       "customers matching doctor" so the LLM treats it as a proper sentence.

    Returns:
        The normalized (spelling-corrected, rephrased) question string.
    """
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


# ---------------------------------------------------------------------------
# STARTUP LOG
# ---------------------------------------------------------------------------
logger.info(f"Using Ollama host: {OLLAMA_HOST}")

# ---------------------------------------------------------------------------
# FASTAPI APPLICATION INSTANCE
# ---------------------------------------------------------------------------
app = FastAPI()

# ---------------------------------------------------------------------------
# CORS MIDDLEWARE
# ---------------------------------------------------------------------------
# Without CORS headers, browsers block requests from a different origin
# (e.g. the React dev server on port 5173 calling our API on port 8000).
#
# allow_origins     - which origins are permitted to make cross-origin requests
# allow_credentials - allows cookies/auth headers to be sent cross-origin
# allow_methods     - which HTTP methods are allowed (GET for reading, POST for writing)
# allow_headers     - which request headers the client is allowed to send
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


# ============================================================================
# READ-ONLY ENDPOINTS (no authentication required)
# ============================================================================

# ---------------------------------------------------------------------------
# GET / — Root status check
# ---------------------------------------------------------------------------
# Returns a simple JSON object confirming the service is running.
# This is useful for load balancers and container orchestration health checks.
@app.get("/")
def root():
    return {"service": "Customer RAG API", "status": "running"}


# ---------------------------------------------------------------------------
# GET /health — Detailed health check
# ---------------------------------------------------------------------------
# Returns a HealthResponse (Pydantic model) with status "healthy".
# Used by Docker and monitoring tools to verify the API is alive.
# The response_model parameter ensures the response matches the schema.
@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="healthy")


# ---------------------------------------------------------------------------
# GET /customers — List customers with optional filters
# ---------------------------------------------------------------------------
# Accepts three optional query parameters to filter results:
#   customer_id - exact match on customer ID
#   segment     - exact match on customer_segment (Silver/Gold/Platinum)
#   product     - exact match on preferred_product
#
# Uses RealDictCursor so each row is returned as a dict, e.g.
#   {"customer_id": 1, "first_name": "John", ...}
#
# The query is constructed dynamically by appending WHERE conditions
# only for the parameters that were provided. Parameterized queries
# (%s placeholders) prevent SQL injection.
@app.get("/customers")
def get_customers(
    customer_id: int = None,
    segment: str = None,
    product: str = None,
):
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
    except Exception:
        # Sanitized error: never leak stack traces or schema details
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# GET /customers/{customer_id} — Single customer by ID
# ---------------------------------------------------------------------------
# Path parameter: customer_id (integer).
# Raises HTTP 404 if no customer with that ID exists.
# The response is a single dict row from the database.
@app.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
):
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
            raise HTTPException(status_code=404, detail="Customer not found")
        return row
    except Exception:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# GET /analytics — Aggregated customer statistics
# ---------------------------------------------------------------------------
# Returns a predefined set of aggregates used by the Dashboard page:
#   - Total customer count
#   - Average annual income (rounded to 2 decimal places)
#   - Count of Platinum, Gold, and Silver segment customers
#
# Uses the AnalyticsResponse Pydantic model for response validation.
# On failure, logs the exception and returns HTTP 500 with a sanitized
# message (no stack trace exposed to the client).
@app.get(
    "/analytics",
    response_model=AnalyticsResponse,
)
def get_analytics():
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


# ---------------------------------------------------------------------------
# GET /analytics/products — Product preference counts
# ---------------------------------------------------------------------------
# GROUP BY preferred_product returns one row per product with a count of
# how many customers prefer that product. RealDictCursor returns rows as
# {"product": "Laptop", "count": 4}.
# Used by the Analytics page's Product Preferences bar chart.
@app.get("/analytics/products")
def get_analytics_products():
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
    except Exception:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# GET /analytics/segments — Segment distribution
# ---------------------------------------------------------------------------
# GROUP BY customer_segment returns one row per segment with a count.
# Returns rows like {"segment": "Gold", "count": 5}.
# Used by the Analytics page's Segment Distribution pie chart.
@app.get("/analytics/segments")
def get_analytics_segments():
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
    except Exception:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# GET /analytics/income — Average income by segment
# ---------------------------------------------------------------------------
# AVG(annual_income)::int casts the average to an integer for cleaner display.
# Returns rows like {"segment": "Gold", "avg_income": 95000}.
# Used by the Analytics page's Income by Segment bar chart.
@app.get("/analytics/income")
def get_analytics_income():
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
    except Exception:
        return {"error": "An internal error occurred"}
    finally:
        if conn:
            conn.close()


# ============================================================================
# WRITE ENDPOINTS
# ============================================================================

# ---------------------------------------------------------------------------
# POST /reindex — Rebuild the ChromaDB vector index
# ---------------------------------------------------------------------------
# This endpoint:
#   1. Fetches ALL customers from PostgreSQL
#   2. Formats each customer into a plain-text document string
#   3. Generates embedding vectors using Ollama (nomic-embed-text)
#   4. Deletes the existing "customers_api" ChromaDB collection
#   5. Creates a fresh collection and adds all documents + embeddings
#
# The ollama and chromadb imports are lazy (inside the function body) so
# the API can start even if these heavy ML packages are not installed.
# This is critical for the Docker image which only installs
# requirements-api.txt at build time.
#
# OLLAMA_HOST points to host.docker.internal:11434 so the container
# reaches Ollama running on the Windows/macOS host machine.
@app.post("/reindex")
def reindex():
    logger.info("Reindex requested")
    conn = None
    try:
        # --- Step 1: Fetch all customers ---
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM customers_rag_safe ORDER BY customer_id;")
        customers = cur.fetchall()
        logger.info("Fetched %d customers from PostgreSQL", len(customers))
        conn.close()
        conn = None

        # --- Step 2: Build document strings ---
        # Each customer record becomes a multi-line string with all fields.
        # These are what ChromaDB indexes and later retrieves for RAG.
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

        # Document IDs match the customer_id so we can trace results back.
        ids = [str(c["customer_id"]) for c in customers]

        # --- Step 3: Generate embeddings ---
        # ollama.embeddings() sends the text to Ollama's nomic-embed-text
        # model and returns a 768-dimensional vector as a list of floats.
        import ollama
        ollama_client = ollama.Client(host=OLLAMA_HOST)
        logger.info("Generating embeddings...")
        embeddings = []
        for doc in documents:
            resp = ollama_client.embeddings(model="nomic-embed-text", prompt=doc)
            embeddings.append(resp["embedding"])
        logger.info("Embeddings generated")

        # --- Step 4: Rebuild ChromaDB collection ---
        # PersistentClient stores data on disk at CHROMA_DB_PATH so it
        # survives container restarts. We delete the old collection first
        # to avoid duplicate vectors, then create a fresh one.
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


# ---------------------------------------------------------------------------
# POST /chat — Hybrid SQL + RAG question answering
# ---------------------------------------------------------------------------
# This is the core intelligence endpoint. It:
#   1. Normalizes the question (spelling correction + single-word wrapping)
#   2. Checks if the question contains SQL keywords
#   3. If yes: tries a hard-coded SQL query. If SQL returns a real answer,
#      return it immediately. If SQL fails (fallback message), fall through.
#   4. If no (or SQL fell through): RAG mode.
#      a. Embed the question using Ollama (nomic-embed-text)
#      b. Query ChromaDB for the 15 most semantically similar documents
#      c. Build a prompt with the retrieved context
#      d. Send to Ollama Qwen2.5-Coder for answer generation
#   5. Return the answer to the client.
#
# ChatRequest validates the body: {"question": "..."} with length 1-2000.
@app.post("/chat")
def chat(
    body: ChatRequest,
):
    try:
        # --- Step 1: Normalize ---
        # Fix typos (docter -> doctor) and wrap single words
        # (doctor -> customers matching doctor)
        question = normalize_question(body.question)

        # --- Step 2: Try SQL routing ---
        if classify_question(question):
            answer = run_sql_query(question)
            # If SQL returned a real answer (not the fallback), return it.
            if "could not find" not in answer:
                return {"answer": answer}
            # Otherwise, fall through to RAG below.

        # --- Step 3: RAG mode ---
        # Lazy imports keep the API startable without heavy ML packages.
        import chromadb
        from chromadb.config import Settings
        import ollama

        # Connect to Ollama running on the host machine
        ollama_client = ollama.Client(host=OLLAMA_HOST)

        # Open the existing ChromaDB collection (must have been indexed
        # via POST /reindex first)
        chroma_client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        collection = chroma_client.get_collection("customers_api")

        # Embed the question so we can search by semantic similarity
        query_emb = ollama_client.embeddings(
            model="nomic-embed-text", prompt=question
        )["embedding"]

        # ChromaDB returns the 15 most similar document vectors using
        # cosine similarity. Each result includes the full document text.
        results = collection.query(
            query_embeddings=[query_emb],
            n_results=15,
        )

        # Debug logging so we can see what ChromaDB found
        logger.info(f"Question: {question}")
        if results.get("documents"):
            logger.info(f"Retrieved docs: {results['documents'][0][:3]}")

        # Join all retrieved documents into a single context block
        context = "\n\n".join(results["documents"][0])

        # Build a prompt that constrains the LLM to answer only from
        # the provided context. This prevents hallucination.
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

        # Ask the LLM to generate an answer based on the context
        response = ollama_client.chat(
            model="qwen2.5-coder:7b",
            messages=[{"role": "user", "content": prompt}],
        )

        return {"answer": response["message"]["content"]}

    except Exception as e:
        return {"error": "An internal error occurred"}
