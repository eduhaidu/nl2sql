from postgres_connection import get_connection

def test_db_connection():
    conn = get_connection()
    if conn:
        print("Database connection successful!")
        conn.close()
    else:
        print("Database connection failed.")

def create_conversation(db_url, database_type=None):
    # Adds a new conversation to the database and returns the conversation ID
    conn = get_connection()
    if not conn:
        print("Failed to connect to the database.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (db_url, database_type, created_at) VALUES (%s, %s, NOW()) RETURNING id;",
            (db_url, database_type)
        )
        conversation_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Conversation created with ID: {conversation_id}")
        return conversation_id
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return None
    finally:        conn.close()

def get_conversations():
    # Retrieves a list of all conversations with their IDs and creation timestamps
    conn = get_connection()
    if not conn:
        print("Failed to connect to the database.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM conversations ORDER BY created_at DESC;")
        conversations = cursor.fetchall()
        print("Conversations:")
        for conv_id, conv_name, created_at in conversations:
            print(f"ID: {conv_id}, Name: {conv_name}, Created At: {created_at}")
        return conversations
    except Exception as e:
        print(f"Error retrieving conversations: {e}")
        return None
    finally:
        conn.close()

def get_conversation_history(conversation_id):
    # Retrieves the conversation history for a given conversation ID
    conn = get_connection()
    if not conn:
        print("Failed to connect to the database.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT message, sender, timestamp FROM conversation_history WHERE conversation_id = %s ORDER BY timestamp;", (conversation_id,))
        history = cursor.fetchall()
        print(f"Conversation history for ID {conversation_id}:")
        for message, sender, timestamp in history:
            print(f"[{timestamp}] {sender}: {message}")
        return history
    except Exception as e:
        print(f"Error retrieving conversation history: {e}")
        return None
    finally:
        conn.close()

def add_message_to_conversation(conversation_id, message, sender):
    # Adds a message to the conversation history for a given conversation ID
    conn = get_connection()
    if not conn:
        print("Failed to connect to the database.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversation_history (conversation_id, message, sender, timestamp) VALUES (%s, %s, %s, NOW());", (conversation_id, message, sender))
        conn.commit()
        print(f"Message added to conversation ID {conversation_id}.")
        return True
    except Exception as e:
        print(f"Error adding message to conversation: {e}")
        return False
    finally:
        conn.close()

def get_conversation_details(conversation_id):
    # Retrieves conversation details including db_url and database_type
    conn = get_connection()
    if not conn:
        print("Failed to connect to the database.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, db_url, database_type, created_at FROM conversations WHERE id = %s;",
            (conversation_id,)
        )
        result = cursor.fetchone()
        if result:
            return {
                "id": result[0],
                "db_url": result[1],
                "database_type": result[2],
                "created_at": result[3]
            }
        return None
    except Exception as e:
        print(f"Error retrieving conversation details: {e}")
        return None
    finally:
        conn.close()

def rename_conversation(conversation_id, new_name):
    # Optional: Add a name column to conversations table and implement renaming functionality
    conn = get_connection()
    if not conn:
        print("Failed to connect to the database.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE conversations SET name = %s WHERE id = %s;", (new_name, conversation_id))
        conn.commit()
        print(f"Conversation ID {conversation_id} renamed to {new_name}.")
        return True
    except Exception as e:
        print(f"Error renaming conversation: {e}")
        return False
    finally:
        conn.close()

def delete_conversation(conversation_id):

    conn = get_connection()
    if not conn:
        print("Failed to connect to the database.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversation_history WHERE conversation_id = %s;", (conversation_id))
        cursor.execute("DELETE FROM conversations WHERE id = %s;", (conversation_id,))
        conn.commit()
        print(f"Conversation ID {conversation_id} and its history deleted.")
        return True
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return False
    finally:
        conn.close()

