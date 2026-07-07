"""
Test executor - communicates with FastAPI backend and executes tests.
Handles session creation, query generation, and result collection.
"""

import requests
import json
import sqlite3
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from urllib.parse import urljoin

from metrics import Metrics


class BackendClient:
    """Client for communicating with NL2SQL FastAPI backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize backend client.
        
        Args:
            base_url: Base URL of FastAPI server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session_id = None
    
    def health_check(self) -> bool:
        """Check if backend is running."""
        try:
            response = requests.get(
                urljoin(self.base_url, "/health"),
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Backend health check failed: {e}")
            return False
    
    def create_session(self, db_url: str, database_type: str = "sqlite", user_id: str = "1") -> Optional[str]:
        """
        Create a new database session.
        
        Args:
            db_url: Database connection string (e.g., sqlite:///path.db)
        
        Returns:
            Session ID or None if failed
        """
        try:
            payload = {
                "database_url": db_url,
                "database_type": database_type,
                "user_id": user_id,
            }
            response = requests.post(
                urljoin(self.base_url, "/dbimport"),
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                print(f"✓ Created session: {self.session_id}")
                return self.session_id
            else:
                print(f"❌ Failed to create session: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Session creation error: {e}")
            return None

    def disconnect_session(self) -> None:
        """Disconnect current backend session to release server-side resources."""
        if not self.session_id:
            return

        try:
            requests.delete(
                urljoin(self.base_url, f"/disconnect/{self.session_id}"),
                timeout=self.timeout,
            )
        except Exception:
            pass
        finally:
            self.session_id = None
    
    def generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Generate SQL from natural language question.
        
        Args:
            question: Natural language question
        
        Returns:
            Response with generated SQL and metadata
        """
        if not self.session_id:
            return {"error": "No active session"}
        
        try:
            response = requests.post(
                urljoin(self.base_url, "/nlinput"),
                json={
                    "nl_input": question,
                    "session_id": self.session_id
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                payload = response.json()
                payload["clean_sql"] = self._select_sql_text(payload)
                return payload
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except requests.Timeout:
            return {"error": "Request timeout"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _select_sql_text(payload: Dict[str, Any]) -> str:
        """Pick the cleanest SQL text from a backend response."""
        candidate = payload.get("query") or payload.get("response") or ""
        return BackendClient._clean_sql_text(candidate)

    @staticmethod
    def _clean_sql_text(sql_text: str) -> str:
        """Strip markdown fences and obvious non-SQL wrappers from a response."""
        if not sql_text:
            return ""

        text = sql_text.strip()
        # Limit the amount of whitespace matched to avoid catastrophic backtracking
        # (protect against ReDoS on very large inputs).
        MAX_WRAP_WS = 1000
        text = re.sub(rf"^```(?:sql)?\s{{0,{MAX_WRAP_WS}}}", "", text, flags=re.IGNORECASE)
        text = re.sub(rf"\s{{0,{MAX_WRAP_WS}}}```$", "", text)

        if "SELECT" in text.upper():
            start = text.upper().find("SELECT")
            text = text[start:]

        return text.strip()
    
    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute SQL query and get results.
        
        Args:
            sql: SQL query to execute
        
        Returns:
            Response with results or error
        """
        if not self.session_id:
            return {"error": "No active session"}
        
        try:
            response = requests.post(
                urljoin(self.base_url, f"/executesql/{self.session_id}"),
                json={"query": sql},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except requests.Timeout:
            return {"error": "Execution timeout"}
        except Exception as e:
            return {"error": str(e)}


class DatabaseSetup:
    """Helpers for local database execution."""

    @staticmethod
    def execute_local_sql(db_path: str, sql: str) -> Dict[str, Any]:
        """Execute SQL directly against a SQLite database file."""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []
            conn.close()

            return {
                "rows": [dict(row) for row in rows],
                "columns": columns,
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def should_preserve_order(expected_sql: str) -> bool:
        """Determine whether row order should matter for comparison."""
        if not expected_sql:
            return False

        normalized_sql = expected_sql.lower()
        return "order by" in normalized_sql or re.search(r"\blimit\b", normalized_sql) is not None

    @staticmethod
    def compare_results(
        expected_rows: List[Dict[str, Any]],
        expected_columns: List[str],
        generated_rows: List[Dict[str, Any]],
        generated_columns: List[str],
        expected_sql: str,
    ) -> bool:
        """Compare result sets with normalization and optional order sensitivity."""
        order_sensitive = DatabaseSetup.should_preserve_order(expected_sql)
        return Metrics.compare_result_sets(
            expected_rows=expected_rows,
            expected_columns=expected_columns,
            generated_rows=generated_rows,
            generated_columns=generated_columns,
            order_sensitive=order_sensitive,
        )


class TestExecutor:
    """Execute a single test case."""
    
    def __init__(self, client: BackendClient, user_id: str = "1"):
        self.client = client
        self.user_id = user_id
    
    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test case.
        
        Args:
            test_case: Test case with question, expected SQL, schema
        
        Returns:
            Result dict with metrics and info
        """
        db_id = test_case["db_id"]
        question = test_case["question"]
        expected_sql = test_case["expected_sql"]
        db_path = test_case["db_path"]
        
        result = {
            "test_id": test_case["id"],
            "db_id": db_id,
            "question": question,
            "expected_sql": expected_sql,
            "generated_sql": None,
            "generated_result": None,
            "execution_success": False,
            "error_message": None,
        }

        db_url = f"sqlite:///{db_path}"

        try:
            if not self.client.create_session(db_url, user_id=self.user_id):
                result["error_message"] = "Session creation failed"
                return result

            expected_response = DatabaseSetup.execute_local_sql(db_path, expected_sql)
            if "error" in expected_response:
                result["error_message"] = f"Expected query error: {expected_response['error']}"
                return result
            
            # Step 2: Generate SQL
            gen_response = self.client.generate_sql(question)
            
            if "error" in gen_response:
                result["error_message"] = f"Generation error: {gen_response['error']}"
                return result
            
            generated_sql = gen_response.get("clean_sql") or gen_response.get("query") or gen_response.get("response", "")
            result["generated_sql"] = generated_sql
            
            # Step 3: Execute generated SQL locally against the same DB
            exec_response = DatabaseSetup.execute_local_sql(db_path, generated_sql)
            if "error" in exec_response:
                result["error_message"] = exec_response["error"]
                return result
            
            # Success!
            result["execution_success"] = True
            result["generated_result"] = exec_response.get("rows", [])
            result["expected_result"] = expected_response.get("rows", [])
            result["result_match"] = DatabaseSetup.compare_results(
                expected_rows=result["expected_result"],
                expected_columns=expected_response.get("columns", []),
                generated_rows=result["generated_result"],
                generated_columns=exec_response.get("columns", []),
                expected_sql=expected_sql,
            )
            
            return result
        finally:
            self.client.disconnect_session()
