from postgres_connection import get_connection
from hash_password import hash_password
import jwt
import dotenv
class AuthController:
    def __init__(self):
        pass

    def authenticate_user(self, username, password):
        conn = get_connection()
        if not conn:
            print("Failed to connect to the database.")
            return False
        try:
            cursor = conn.cursor()
            if not username or not password:
                print("Username or password cannot be empty.")
                return False 
            if self.check_sql_injection(username) or self.check_sql_injection(password):
                print("SQL injection attempt detected. Authentication failed.")
                return False
            cursor.execute("SELECT password FROM users WHERE username = %s;", (username,))
            result = cursor.fetchone()
            if result and result[0] == hash_password(password):
                print(f"User {username} authenticated successfully.")
                token = jwt.encode({"username": username}, dotenv.get_key(".env", "JWT_SECRET_KEY"), algorithm="HS256")
                user_id = self.get_user_id(username)
                print(f"Generated JWT token for user {username}: {token}")
                return {"message": "Authentication successful", "token": token, "user_id": user_id}
            else:
                print(f"Authentication failed for user {username}.")
                return False
        except Exception as e:
            print(f"Error during authentication: {e}")
            return False
        finally:            conn.close()

    def register_user(self, username, password):
        conn = get_connection()
        if not conn:
            print("Failed to connect to the database.")
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s;", (username,))
            result = cursor.fetchone()
            if result:
                print(f"Username {username} already exists.")
                return False
            hashed_password = hash_password(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s);", (username, hashed_password))
            conn.commit()
            print(f"User {username} registered successfully.")
            token = jwt.encode({"username": username}, dotenv.get_key(".env", "JWT_SECRET_KEY"), algorithm="HS256")
            user_id = self.get_user_id(username)
            print(f"Generated JWT token for new user {username} (ID: {user_id}): {token}")
            return {"message": "Registration successful", "token": token, "user_id": user_id}
        except Exception as e:
            print(f"Error during registration: {e}")
            return False
        finally:            conn.close()

    def get_user_id(self, username):
        conn = get_connection()
        if not conn:
            print("Failed to connect to the database.")
            return None
        try:
            cursor = conn.cursor()
            if not username:
                print("Username cannot be empty.")
                return None
            if self.check_sql_injection(username):
                print("SQL injection attempt detected. Cannot retrieve user ID.")
                return None
            cursor.execute("SELECT id FROM users WHERE username = %s;", (username,))
            result = cursor.fetchone()
            if result:
                print(f"User ID for {username} is {result[0]}.")
                return result[0]
            else:
                print(f"User {username} not found.")
                return None
        except Exception as e:
            print(f"Error retrieving user ID: {e}")
            return None
        finally:
            conn.close()
    def logout_user(self, token):
        # In a real application, you would implement token blacklisting or expiration to handle logout
        print(f"User logged out with token: {token}")
        return {"message": "Logout successful"}
    
    def refresh_token(self, token):
        try:
            decoded = jwt.decode(token, dotenv.get_key(".env", "JWT_SECRET_KEY"), algorithms=["HS256"])
            username = decoded.get("username")
            if username:
                new_token = jwt.encode({"username": username}, dotenv.get_key(".env", "JWT_SECRET_KEY"), algorithm="HS256")
                print(f"Token refreshed for user {username}: {new_token}")
                return {"message": "Token refreshed", "token": new_token}
            else:
                print("Invalid token: username not found.")
                return False
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
            return False
        except jwt.InvalidTokenError:
            print("Invalid token.")
            return False
        
    def check_sql_injection(self, input_string):
        if " OR " in input_string or ";" in input_string or "--" in input_string:
            print("SQL injection attempt detected.")
            return True
        return False