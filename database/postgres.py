import os
from config import settings
from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor


# Load the environment variables from your .env file
# load_dotenv()

DATABASE_URL = settings.database_url

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database.
    Using RealDictCursor returns database rows as Python dictionaries (like JS objects),
    instead of default tuples.
    """
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def test_connection():
    """
    Simple helper to test if our connection string works.
    """
    try:
        # 1. Connect
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 2. Execute a test query
        cur.execute("SELECT version();")
        result: Any = cur.fetchone()
        
        print("✅ Successfully connected to Supabase PostgreSQL!")
        if result:
            print(f"Database version: {result['version']}")

        
        # 3. Clean up
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ Error connecting to the database:")
        print(e)

# This block only runs if you run this file directly (e.g. python postgres.py)
if __name__ == "__main__":
    test_connection()