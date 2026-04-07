from postgres_connection import get_connection
from hash_password import hash_password
import jwcrypto
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
            cursor.execute("SELECT password FROM users WHERE username = %s;", (username,))
            result = cursor.fetchone()
            if result and result[0] == hash_password(password):
                print(f"User {username} authenticated successfully.")
                token = jwcrypto.jwt.JWT(header={"alg": "HS256"}, claims={"username": username}).make_signed_token(jwcrypto.jwk.JWK.from_password(dotenv.get_key(".env", "JWT_SECRET_KEY")))
                user_id = self.get_user_id(username)
                print(f"Generated JWT token for user {username}: {token.serialize()}")
                return {"message": "Authentication successful", "token": token.serialize(), "user_id": user_id}
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
            token = jwcrypto.jwt.JWT(header={"alg": "HS256"}, claims={"username": username}).make_signed_token(jwcrypto.jwk.JWK.from_password(dotenv.get_key(".env", "JWT_SECRET_KEY")))
            user_id = self.get_user_id(username)
            print(f"Generated JWT token for new user {username} (ID: {user_id}): {token.serialize()}")
            return {"message": "Registration successful", "token": token.serialize(), "user_id": user_id}
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