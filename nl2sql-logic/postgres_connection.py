import psycopg2
import os

def get_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("POSTGRESQL_HOST", "localhost"),
            port=os.getenv("POSTGRESQL_PORT", 5432),
            database=os.getenv("POSTGRESQL_DATABASE", "nl2sqldb"),
            user=os.getenv("POSTGRESQL_USER", "eduhaidu"),
            password=os.getenv("POSTGRESQL_PASSWORD", "")
        )
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

