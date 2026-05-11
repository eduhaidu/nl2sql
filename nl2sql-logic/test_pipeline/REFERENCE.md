"""
Test Pipeline Structure & Quick Reference
"""

# FILE STRUCTURE

# ==============

test_pipeline/
├── dataset_loader.py # Load Spider/Bird datasets
├── executor.py # Execute tests against backend
├── metrics.py # Calculate evaluation metrics
├── runner.py # Main orchestrator (entry point)
├── example.py # Usage examples
├── quickstart.py # Setup validation
├── requirements.txt # Python dependencies
├── README.md # Full documentation
└── test_results/ # Generated output directory

# QUICK START

# ===========

# 1. Install dependencies

pip install -r requirements.txt

# 2. Validate setup (optional)

python quickstart.py

# 3. Run 10 test cases (quick validation)

python runner.py --dataset /path/to/spider --limit 10 -v

# 4. Run full dev set

python runner.py --dataset /path/to/spider

# 5. View results

cat test*results/results*\*.json | python -m json.tool

# COMMAND-LINE OPTIONS

# ====================

python runner.py \
 --dataset /path/to/spider # REQUIRED: Dataset directory
--backend http://localhost:8000 # Optional: Backend URL
--limit 100 # Optional: Test limit (for quick runs)
--output /path/to/results # Optional: Output directory
-v, --verbose # Optional: Detailed output

# EXAMPLE RUNS

# ============

# Test with 20 examples from dev set

python runner.py --dataset ~/spider --limit 20

# Test full dataset, save to custom location

python runner.py --dataset ~/spider --output ./eval_results

# Verbose mode to see generated SQL

python runner.py --dataset ~/spider --limit 5 -v

# Point to different backend

python runner.py --dataset ~/spider --backend http://localhost:8001 --limit 50

# KEY MODULES

# ===========

1. dataset_loader.py
   - DatasetLoader class
   - Methods:
     - load() - Load questions from JSON
     - load_databases() - Load schema definitions
     - get_test_cases() - Get test cases with limit

2. executor.py
   - BackendClient - HTTP client for API
     - health_check() - Verify backend running
     - create_session(db_url) - Create new database session
     - generate_sql(question) - Generate SQL from question
     - execute_sql(sql) - Execute SQL and get results
   - DatabaseSetup - Create test databases
     - create_test_db(schema) - Create SQLite from schema
   - TestExecutor - Run individual tests
     - run_test(test_case) - Execute single test

3. metrics.py
   - Metrics class - Static evaluation functions
     - exact_match() - String comparison
     - result_match() - Compare query results
     - semantic_match() - Token-level similarity
   - TestResult - Store individual test result
   - AggregateMetrics - Aggregate statistics
     - execution_accuracy() - % successful executions
     - exact_match_accuracy() - % exact SQL matches
     - result_match_accuracy() - % correct results
     - avg_semantic_similarity() - Average similarity score
     - print_report() - Print formatted report

4. runner.py
   - PipelineRunner - Main orchestrator
     - run() - Execute full pipeline
     - \_save_results() - Save results to JSON

# OUTPUT EXAMPLE

# ==============

============================================================
EVALUATION REPORT
============================================================
Total Tests: 1034
Execution Success: 856/1034 (82.8%)
Exact Match (EM): 342/1034 (33.1%)
Result Match: 612/1034 (59.2%)
Avg Semantic Sim: 0.72

Top Errors:
Timeout: 95
Syntax error: 42
Table not found: 28

Results by Database:
concert_singer | 55 tests | 87.3% success | 38.2% EM
pets_and_owners | 48 tests | 84.2% success | 31.2% EM
============================================================

Results saved to: test_results/results_20260430_143022.json

# METRICS EXPLAINED

# =================

Execution Accuracy (%)

- Percentage of queries that ran without error
- Good baseline: 70-85%
- Target: >90%

Exact Match (EM) (%)

- Percentage of generated SQL matching expected SQL
- Human performance on Spider: ~80%
- State-of-art models: ~40-50%
- Baseline expectation: 15-30%

Result Match (%)

- Percentage of queries returning correct results
- Requires both correct SQL AND correct execution
- More difficult than EM

Semantic Similarity (0-1)

- Token overlap between generated and expected SQL
- 1.0 = perfect, 0.8+ = very similar, <0.5 = different approach
- Useful for cases that aren't exact but are close

# CUSTOMIZATION

# ==============

1. Change timeout in executor.py:
   self.timeout = 60 # seconds

2. Adjust test database size in executor.py:

   # For larger test DBs, seed with data

3. Add custom metrics in metrics.py:
   @staticmethod
   def my_metric(sql1, sql2): # Your implementation
   return score

4. Change similarity threshold in metrics.py:
   if similarity > 0.4: # Adjust threshold

5. Modify report format in metrics.py:
   def print_report(self): # Customize output

# EXAMPLE USAGE (Python)

# ======================

from runner import PipelineRunner

runner = PipelineRunner(
dataset_path="/path/to/spider",
backend_url="http://localhost:8000",
output_dir="results"
)

runner.run(limit=50, verbose=True)

# Or use components separately:

from dataset_loader import DatasetLoader
from executor import BackendClient, TestExecutor
from metrics import Metrics

loader = DatasetLoader("/path/to/spider")
test_cases = loader.get_test_cases(limit=5)

client = BackendClient("http://localhost:8000")
executor = TestExecutor(client)

for test_case in test_cases:
result = executor.run_test(test_case)

    # Calculate metrics
    exact = Metrics.exact_match(
        result["generated_sql"],
        result["expected_sql"]
    )
    print(f"Test: {exact}")

# TROUBLESHOOTING

# ===============

Backend connection error:
→ Start backend: cd .. && python main.py

Dataset not found:
→ Check path: ls /path/to/spider/dev.json

Timeout during execution:
→ Increase timeout in executor.py
→ Use --limit to run fewer tests

Out of memory:
→ Use --limit to run in smaller batches
→ Process batches sequentially

Request timeout from backend:
→ Increase timeout in runner.py
→ Check if Ollama is running (if using local model)

# PERFORMANCE

# ===========

Typical timing (per query):

- Ollama inference: 5-15 seconds
- Database setup: 0.5-1 second
- Result retrieval: 0.1-0.5 seconds
- Total per query: 6-16 seconds

For full Spider (1034 tests):

- Estimated time: 2-4 hours
- Total queries: 1034
- Storage needed: ~50-100 MB for results

Use --limit for quick runs:

- 10 tests: ~2 minutes
- 50 tests: ~10 minutes
- 100 tests: ~20 minutes

# NEXT STEPS FOR FULL IMPLEMENTATION

# ===================================

1. Real result comparison (row-by-row)
2. Multi-database support (PostgreSQL, MySQL)
3. Error classification and categorization
4. Parallel test execution
5. Performance monitoring per query type
6. Multi-turn conversation testing
7. Regression testing for CI/CD
8. Model hyperparameter tuning
9. Result caching for faster iterations

# REFERENCE LINKS

# ===============

Spider Dataset: https://yale-lily.github.io/spider
Bird Dataset: https://bird-bench.github.io/
FastAPI: https://fastapi.tiangolo.com/
Requests: https://docs.python-requests.org/
"""
