"""
Dataset loader for Spider and Bird benchmarks.
Handles parsing and organizing test cases.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any


class DatasetLoader:
    """Load Spider/Bird datasets from JSON files."""
    
    def __init__(self, dataset_path: str, split: str = "train"):
        """
        Initialize dataset loader.
        
        Args:
            dataset_path: Path to dataset directory (contains train.json, dev.json, etc.)
            split: Which split to load ("train", "dev", "test")
        """
        self.dataset_path = Path(dataset_path)
        self.database_root = self.dataset_path / "database"
        self.split = split
        self.questions = []
        self.databases = {}
        
    def load(self) -> List[Dict[str, Any]]:
        """
        Load and parse dataset.
        
        Expected structure:
        {
            "db_id": "database_name",
            "question": "What is...",
            "query": "SELECT ...",
            "query_toks": [...],
            ...
        }
        """
        json_file = self.dataset_path / f"{self.split}.json"
        
        if not json_file.exists():
            raise FileNotFoundError(f"Dataset file not found: {json_file}")
        
        with open(json_file, 'r') as f:
            self.questions = json.load(f)
        
        print(f"✓ Loaded {len(self.questions)} questions from {self.split} split")
        return self.questions
    
    def load_databases(self) -> Dict[str, Dict[str, Any]]:
        """
        Load database schemas from tables.json.
        
        Expected structure:
        {
            "db_id": "database_name",
            "table_names_original": ["table1", "table2", ...],
            "column_names_original": [[0, "col1"], [1, "col2"], ...],
            "primary_keys": [...],
            "foreign_keys": [...],
            ...
        }
        """
        tables_file = self.dataset_path / "tables.json"
        
        if not tables_file.exists():
            raise FileNotFoundError(f"Tables file not found: {tables_file}")
        
        with open(tables_file, 'r') as f:
            tables_data = json.load(f)
        
        # Index by db_id for fast lookup
        for db_info in tables_data:
            self.databases[db_info["db_id"]] = db_info
        
        print(f"✓ Loaded {len(self.databases)} database schemas")
        return self.databases
    
    def get_test_cases(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get test cases with enhanced schema information.
        
        Returns:
            List of test cases with question, expected SQL, and schema.
        """
        if not self.questions:
            self.load()
        if not self.databases:
            self.load_databases()
        
        test_cases = []
        for i, question in enumerate(self.questions):
            if limit and i >= limit:
                break
            
            db_id = question.get("db_id")
            schema = self.databases.get(db_id)
            db_path = self.get_database_path(db_id)
            
            if not schema:
                print(f"⚠ Warning: Schema not found for {db_id}")
                continue
            if not db_path:
                print(f"⚠ Warning: Database file not found for {db_id}")
                continue
            
            test_cases.append({
                "id": i,
                "db_id": db_id,
                "question": question.get("question", ""),
                "expected_sql": question.get("query", ""),
                "schema": schema,
                "db_path": str(db_path),
            })
        
        return test_cases

    def get_database_path(self, db_id: str) -> Path:
        """Return the SQLite file path for a Spider database ID."""
        if not db_id:
            return None

        candidates = [
            self.database_root / db_id / f"{db_id}.sqlite",
            self.database_root / db_id / f"{db_id}.db",
            self.database_root / db_id / f"{db_id}.sqlite3",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        if self.database_root.exists():
            for extension in ("*.sqlite", "*.db", "*.sqlite3"):
                matches = list((self.database_root / db_id).glob(extension)) if (self.database_root / db_id).exists() else []
                if matches:
                    return matches[0]

        return None


if __name__ == "__main__":
    # Example usage
    loader = DatasetLoader("/path/to/spider", split="dev")
    loader.load()
    loader.load_databases()
    
    test_cases = loader.get_test_cases(limit=5)
    for tc in test_cases:
        print(f"\nDB: {tc['db_id']}")
        print(f"Q: {tc['question']}")
        print(f"SQL: {tc['expected_sql']}")
