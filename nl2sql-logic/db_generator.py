import sqlite3
from datetime import datetime, timedelta
import random

def generate_database(schema_sql, table_data, db_name='test_databases/sample.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.executescript(schema_sql)
    conn.commit()

    for table_name, rows in table_data.items():
        if not rows:
            continue
        columns = ', '.join(rows[0].keys())
        placeholders = ', '.join(['?' for _ in rows[0]])
        insert_query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
        values = [tuple(row.values()) for row in rows]
        cursor.executemany(insert_query, values)
        conn.commit()
    return conn

def generate_sample_data():
    users = []
    for i in range(1, 11):
        users.append({
            'id': i,
            'name': f'User{i}',
            'email': f'user{i}@example.com'
        })
    orders = []
    for i in range(1, 21):
        orders.append({
            'id': i,
            'user_id': random.randint(1, 10),
            'product': f'Product{random.randint(1, 5)}',
            'amount': round(random.uniform(10.0, 100.0), 2),
            'order_date': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        })
    return {
        'users': users,
        'orders': orders
    }
schema_sql = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product TEXT NOT NULL,
    amount REAL NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""
table_data = generate_sample_data()
db_connection = generate_database(schema_sql, table_data)
# Example usage: Query the database to verify data insertion
cursor = db_connection.cursor()
cursor.execute("SELECT * FROM users;")
users = cursor.fetchall()
for user in users:
    print(user)
cursor.execute("SELECT * FROM orders;")
orders = cursor.fetchall()
for order in orders:
    print(order)


if __name__ == "__main__":
    # Example usage: Query the database to verify data insertion
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM users;")
    users = cursor.fetchall()
    for user in users:
        print(user)
    cursor.execute("SELECT * FROM orders;")
    orders = cursor.fetchall()
    for order in orders:
        print(order)