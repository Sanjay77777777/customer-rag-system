# ---------------------------------------------------------------------------
# DATABASE CONNECTION MODULE
# ---------------------------------------------------------------------------
# This module provides the get_connection() function used by every endpoint
# that needs to query PostgreSQL. Credentials are read from the .env file
# via python-dotenv, keeping secrets out of the source code.
#
# The .env file is gitignored and must contain:
#   POSTGRES_HOST=host.docker.internal
#   POSTGRES_PORT=5432
#   POSTGRES_DB=customerdb
#   POSTGRES_USER=postgres
#   POSTGRES_PASSWORD=your_password

import os

# psycopg2 is the official PostgreSQL adapter for Python.
# It handles connection pooling, parameterized queries, and type casting.
import psycopg2

# extras provides RealDictCursor (returns rows as dicts) and other utilities.
import psycopg2.extras

# python-dotenv loads environment variables from a .env file into
# os.environ so they are available throughout the application.
from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file).
# This must be called before any code reads os.environ values.
load_dotenv()


def get_connection():
    """Create and return a new PostgreSQL connection using .env settings.

    Each call creates a fresh connection. The caller is responsible for
    closing it (typically in a try/finally block).

    Uses os.environ[] (not os.getenv()) so missing variables raise a
    KeyError immediately rather than silently returning None.

    Returns:
        psycopg2.connection object.
    """
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        # PORT is stored as a string in .env but psycopg2 expects an int.
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
