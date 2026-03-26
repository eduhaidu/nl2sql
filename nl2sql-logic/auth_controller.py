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
                print(f"Generated JWT token for user {username}: {token.serialize()}")
                return {"message": "Authentication successful", "token": token.serialize()}
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
            return {"message": "Registration successful", "token": token.serialize()}
        except Exception as e:
            print(f"Error during registration: {e}")
            return False
        finally:            conn.close()