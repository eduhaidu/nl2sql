"""
Evaluation metrics for NL-to-SQL systems.
Handles accuracy calculations and result comparisons.
"""

import re
from typing import Any, List, Dict, Tuple
from difflib import SequenceMatcher


class Metrics:
    """Calculate various accuracy metrics for SQL generation."""

    @staticmethod
    def normalize_value(value: Any) -> Any:
        """Normalize a single SQL result cell for comparison."""
        if value is None:
            return None

        if isinstance(value, bool):
            return int(value)

        if isinstance(value, (int, float)):
            return Metrics._normalize_number(value)

        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")

        if isinstance(value, str):
            stripped = value.strip()
            numeric_value = Metrics._try_parse_number(stripped)
            return numeric_value if numeric_value is not None else stripped

        return str(value).strip()

    @staticmethod
    def normalize_rows(rows: List[Dict[str, Any]], columns: List[str]) -> List[tuple]:
        """Convert query result rows into normalized tuples using column order."""
        normalized_rows = []
        for row in rows:
            normalized_rows.append(
                tuple(Metrics.normalize_value(row.get(column)) for column in columns)
            )
        return normalized_rows

    @staticmethod
    def compare_result_sets(
        expected_rows: List[Dict[str, Any]],
        expected_columns: List[str],
        generated_rows: List[Dict[str, Any]],
        generated_columns: List[str],
        order_sensitive: bool = False,
    ) -> bool:
        """Compare two SQL result sets after normalization."""
        if len(expected_rows) != len(generated_rows):
            return False

        if not expected_rows and not generated_rows:
            return True

        expected_normalized = Metrics.normalize_rows(expected_rows, expected_columns)
        generated_normalized = Metrics.normalize_rows(generated_rows, generated_columns)

        if order_sensitive:
            return expected_normalized == generated_normalized

        return sorted(expected_normalized, key=Metrics._row_sort_key) == sorted(
            generated_normalized,
            key=Metrics._row_sort_key,
        )
    
    @staticmethod
    def exact_match(generated_sql: str, expected_sql: str) -> bool:
        """
        Check if generated SQL exactly matches expected SQL (string comparison).
        
        This is strict but doesn't account for query equivalence.
        """
        gen_normalized = Metrics._normalize_sql(generated_sql)
        exp_normalized = Metrics._normalize_sql(expected_sql)
        return gen_normalized == exp_normalized
    
    @staticmethod
    def result_match(
        generated_result: List[Dict[str, Any]], 
        expected_result: List[Dict[str, Any]]
    ) -> Tuple[bool, float]:
        """
        Compare query results.
        
        Returns:
            (matches: bool, similarity: float from 0-1)
        """
        expected_columns = list(expected_result[0].keys()) if expected_result else []
        generated_columns = list(generated_result[0].keys()) if generated_result else []
        matches = Metrics.compare_result_sets(
            expected_rows=expected_result,
            expected_columns=expected_columns,
            generated_rows=generated_result,
            generated_columns=generated_columns,
            order_sensitive=False,
        )
        return matches, 1.0 if matches else 0.0
    
    @staticmethod
    def semantic_match(generated_sql: str, expected_sql: str) -> float:
        """
        Rough semantic similarity using token-level overlap.
        
        Returns:
            Similarity score 0-1
        """
        gen_tokens = Metrics._extract_tokens(generated_sql)
        exp_tokens = Metrics._extract_tokens(expected_sql)
        
        if not gen_tokens and not exp_tokens:
            return 1.0
        
        common = len(gen_tokens & exp_tokens)
        total = len(gen_tokens | exp_tokens)
        
        return common / total if total > 0 else 0.0
    
    @staticmethod
    def _normalize_sql(sql: str) -> str:
        """Normalize SQL for comparison (whitespace, case)."""
        if not sql:
            return ""
        
        # Remove leading/trailing whitespace
        sql = sql.strip()
        
        # Normalize whitespace
        sql = re.sub(r'\s+', ' ', sql)
        
        # Lowercase keywords (but not values)
        # This is a simple heuristic; not foolproof
        sql = re.sub(
            r'\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|ON|GROUP|BY|ORDER|HAVING|DISTINCT|AS)\b',
            lambda m: m.group(1).lower(),
            sql,
            flags=re.IGNORECASE
        )
        
        return sql.strip()
    
    @staticmethod
    def _extract_tokens(sql: str) -> set:
        """Extract meaningful tokens from SQL."""
        # Remove punctuation except for underscores
        tokens = re.findall(r'\b\w+\b', sql.lower())
        # Filter out common keywords that don't add semantic value
        keywords = {'select', 'from', 'where', 'and', 'or', 'join', 'on', 'as', 'distinct'}
        return set(t for t in tokens if t not in keywords)

    @staticmethod
    def _normalize_number(value: Any) -> Any:
        """Normalize numeric values for stable comparisons."""
        if isinstance(value, bool):
            return int(value)

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            return float(f"{value:.15g}")

        return value

    @staticmethod
    def _try_parse_number(value: str) -> Any:
        """Parse numeric strings when they clearly represent numbers."""
        if not value:
            return None

        if re.fullmatch(r"[-+]?\d+", value):
            try:
                return int(value)
            except ValueError:
                return None

        if re.fullmatch(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?", value) or re.fullmatch(r"[-+]?\d+(?:[eE][-+]?\d+)", value):
            try:
                parsed = float(value)
                return int(parsed) if parsed.is_integer() else float(f"{parsed:.15g}")
            except ValueError:
                return None

        return None

    @staticmethod
    def _row_sort_key(row: tuple) -> tuple:
        """Build a deterministic, type-safe sort key for normalized result rows."""
        return tuple(Metrics._value_sort_key(value) for value in row)

    @staticmethod
    def _value_sort_key(value: Any) -> tuple:
        """Convert possibly mixed-type values into a consistently sortable key."""
        if value is None:
            return (0, "")

        if isinstance(value, bool):
            return (1, int(value))

        if isinstance(value, int):
            return (2, value)

        if isinstance(value, float):
            return (3, value)

        if isinstance(value, bytes):
            return (4, value.decode("utf-8", errors="ignore"))

        return (5, str(value))


class TestResult:
    """Store and track individual test result."""
    
    def __init__(self, test_id: int, db_id: str, question: str):
        self.test_id = test_id
        self.db_id = db_id
        self.question = question
        
        self.expected_sql = None
        self.generated_sql = None
        self.generated_result = None
        self.expected_result = None
        
        self.execution_success = False
        self.error_message = None
        
        # Metrics
        self.exact_match_score = False
        self.result_match_score = False
        self.semantic_match_score = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "test_id": self.test_id,
            "db_id": self.db_id,
            "question": self.question,
            "expected_sql": self.expected_sql,
            "generated_sql": self.generated_sql,
            "expected_result": self.expected_result,
            "generated_result": self.generated_result,
            "execution_success": self.execution_success,
            "error_message": self.error_message,
            "exact_match": self.exact_match_score,
            "result_match": self.result_match_score,
            "semantic_match": self.semantic_match_score,
        }


class AggregateMetrics:
    """Aggregate metrics across all tests."""
    
    def __init__(self):
        self.total_tests = 0
        self.successful_executions = 0
        self.exact_matches = 0
        self.result_matches = 0
        self.semantic_similarities = []
        
        self.error_types = {}  # Count error types
        self.results_by_db = {}  # Results grouped by database
    
    def add_result(self, result: TestResult) -> None:
        """Add a test result to aggregation."""
        self.total_tests += 1
        
        if result.execution_success:
            self.successful_executions += 1
        
        if result.exact_match_score:
            self.exact_matches += 1
        
        if result.result_match_score:
            self.result_matches += 1
        
        if result.semantic_match_score > 0:
            self.semantic_similarities.append(result.semantic_match_score)
        
        if result.error_message:
            error_type = result.error_message.split(':')[0]
            self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
        
        # Track by database
        if result.db_id not in self.results_by_db:
            self.results_by_db[result.db_id] = {
                "total": 0,
                "execution_success": 0,
                "exact_matches": 0,
            }
        
        self.results_by_db[result.db_id]["total"] += 1
        if result.execution_success:
            self.results_by_db[result.db_id]["execution_success"] += 1
        if result.exact_match_score:
            self.results_by_db[result.db_id]["exact_matches"] += 1
    
    def execution_accuracy(self) -> float:
        """Percentage of queries that executed without error."""
        return self.successful_executions / self.total_tests if self.total_tests > 0 else 0.0
    
    def exact_match_accuracy(self) -> float:
        """Percentage of exact SQL matches."""
        return self.exact_matches / self.total_tests if self.total_tests > 0 else 0.0
    
    def result_match_accuracy(self) -> float:
        """Percentage of matching results."""
        return self.result_matches / self.total_tests if self.total_tests > 0 else 0.0
    
    def avg_semantic_similarity(self) -> float:
        """Average semantic similarity score."""
        return sum(self.semantic_similarities) / len(self.semantic_similarities) if self.semantic_similarities else 0.0
    
    def print_report(self) -> None:
        """Print formatted report."""
        print("\n" + "="*60)
        print("EVALUATION REPORT")
        print("="*60)
        print(f"Total Tests:            {self.total_tests}")
        print(f"Execution Success:      {self.successful_executions}/{self.total_tests} ({self.execution_accuracy():.1%})")
        print(f"Exact Match (EM):       {self.exact_matches}/{self.total_tests} ({self.exact_match_accuracy():.1%})")
        print(f"Result Match:           {self.result_matches}/{self.total_tests} ({self.result_match_accuracy():.1%})")
        print(f"Avg Semantic Sim:       {self.avg_semantic_similarity():.2f}")
        
        if self.error_types:
            print("\nTop Errors:")
            for error_type, count in sorted(self.error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {error_type}: {count}")
        
        if self.results_by_db:
            print("\nResults by Database:")
            for db_id, stats in sorted(self.results_by_db.items()):
                success_rate = stats["execution_success"] / stats["total"] if stats["total"] > 0 else 0
                em_rate = stats["exact_matches"] / stats["total"] if stats["total"] > 0 else 0
                print(f"  {db_id:15} | {stats['total']:3} tests | {success_rate:.1%} success | {em_rate:.1%} EM")
        
        print("="*60 + "\n")
