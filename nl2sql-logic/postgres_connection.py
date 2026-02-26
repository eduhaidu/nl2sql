import psycopg2

def get_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            port=5432,
            database="nl2sqldb",
            user="eduhaidu",
            password="" 
        )
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

