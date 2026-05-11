"""
Example usage and debugging script for test pipeline components.
Useful for development and manual testing.
"""

from dataset_loader import DatasetLoader
from executor import BackendClient, TestExecutor, DatabaseSetup
from metrics import Metrics, TestResult


def example_load_dataset():
    """Example 1: Load dataset"""
    print("Example 1: Loading Dataset")
    print("-" * 40)
    
    loader = DatasetLoader("/path/to/spider", split="dev")
    questions = loader.load()
    databases = loader.load_databases()
    
    print(f"Loaded {len(questions)} questions")
    print(f"Loaded {len(databases)} database schemas")
    
    # Get first 3 test cases
    test_cases = loader.get_test_cases(limit=3)
    for tc in test_cases:
        print(f"\n  DB: {tc['db_id']}")
        print(f"  Q: {tc['question']}")
        print(f"  SQL: {tc['expected_sql'][:60]}...")


def example_backend_client():
    """Example 2: Use backend client"""
    print("\n\nExample 2: Backend Client")
    print("-" * 40)
    
    client = BackendClient("http://localhost:8000")
    
    # Check health
    if not client.health_check():
        print("❌ Backend not running")
        return
    print("✓ Backend is healthy")
    
    # Create session (requires valid db_url)
    db_url = "sqlite:///example.db"
    session_id = client.create_session(db_url)
    if session_id:
        print(f"✓ Created session: {session_id}")


def example_metrics():
    """Example 3: Calculate metrics"""
    print("\n\nExample 3: Metrics Calculation")
    print("-" * 40)
    
    expected = "SELECT COUNT(*) FROM users WHERE age > 21"
    generated = "select count(*) from users where age > 21"
    
    # Exact match (after normalization)
    exact = Metrics.exact_match(expected, generated)
    print(f"Exact match: {exact}")
    
    # Semantic similarity
    generated2 = "SELECT COUNT(*) FROM users WHERE age >= 22"
    sim = Metrics.semantic_match(expected, generated2)
    print(f"Semantic similarity (different threshold): {sim:.2f}")
    
    generated3 = "SELECT id FROM users"
    sim2 = Metrics.semantic_match(expected, generated3)
    print(f"Semantic similarity (completely different): {sim2:.2f}")


def example_database_setup():
    """Example 4: Create test database"""
    print("\n\nExample 4: Database Setup")
    print("-" * 40)
    
    # Simple test schema
    schema = {
        "db_id": "test_db",
        "table_names_original": ["users", "orders"],
        "column_names_original": [
            [0, "id"],
            [0, "name"],
            [0, "email"],
            [1, "id"],
            [1, "user_id"],
            [1, "total"],
        ]
    }
    
    db_url = DatabaseSetup.create_test_db(schema, db_name="test_example.db")
    print(f"Created database: {db_url}")


def example_pipeline_minimal():
    """Example 5: Minimal pipeline (no backend needed)"""
    print("\n\nExample 5: Minimal Pipeline (Metrics Only)")
    print("-" * 40)
    
    # Simulate test results
    test_results = [
        {
            "expected": "SELECT * FROM users WHERE id = 1",
            "generated": "SELECT * FROM users WHERE id = 1",
            "label": "Perfect match"
        },
        {
            "expected": "SELECT * FROM users WHERE age > 18",
            "generated": "SELECT * FROM users WHERE age >= 19",
            "label": "Similar but not exact"
        },
        {
            "expected": "SELECT COUNT(*) FROM orders GROUP BY user_id",
            "generated": "SELECT COUNT(id) FROM orders GROUP BY user_id",
            "label": "Functionally equivalent"
        },
    ]
    
    for result in test_results:
        expected = result["expected"]
        generated = result["generated"]
        
        exact = Metrics.exact_match(expected, generated)
        semantic = Metrics.semantic_match(expected, generated)
        
        print(f"\n{result['label']}")
        print(f"  Expected:  {expected}")
        print(f"  Generated: {generated}")
        print(f"  Exact:     {exact}")
        print(f"  Semantic:  {semantic:.2f}")


if __name__ == "__main__":
    print("=" * 60)
    print("NL2SQL Test Pipeline - Examples")
    print("=" * 60)
    
    # Run examples
    # Uncomment to run (requires dataset and backend availability)
    
    # example_load_dataset()
    # example_backend_client()
    example_metrics()
    # example_database_setup()
    example_pipeline_minimal()
    
    print("\n" + "=" * 60)
    print("For full pipeline run:")
    print("  python runner.py --dataset /path/to/spider --limit 10 -v")
    print("=" * 60)
