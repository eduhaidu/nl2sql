# NL2SQL Test Pipeline

Automated testing framework for evaluating NL-to-SQL performance on Spider/Bird benchmarks.

## Overview

This MVP pipeline provides:

- **Dataset Loading** — Parse Spider/Bird JSON format
- **Test Execution** — Generate SQL, execute queries, collect results
- **Evaluation Metrics** — Exact match (EM), execution accuracy, semantic similarity
- **Reporting** — Per-database and aggregate statistics

## Architecture

```
┌─────────────────────────────────────────────────┐
│ runner.py (Orchestrator)                        │
│ - Loads test cases                              │
│ - Manages pipeline flow                         │
│ - Aggregates metrics                            │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┴───────┬────────────┬────────────┐
       │               │            │            │
   ┌───▼─────┐  ┌──────▼───┐  ┌────▼────┐  ┌───▼───────┐
   │ dataset │  │ executor │  │ metrics │  │ backend   │
   │ _loader │  │          │  │         │  │ _client   │
   └─────────┘  └──────────┘  └─────────┘  └───────────┘
```

## Setup

### 1. Install Dependencies

```bash
cd test_pipeline
pip install -r requirements.txt
```

### 2. Prepare Spider Dataset

Download Spider dataset from: https://yale-lily.github.io/spider

```bash
# Expected structure:
spider/
  ├── train.json          # Training examples
  ├── dev.json           # Dev examples
  ├── tables.json        # Schema definitions
  └── database/          # Database files (optional)
```

### 3. Start Backend

From the main project directory:

```bash
cd ..
python main.py
```

Backend should start on `http://localhost:8000`

## Quick Start

### Run Quick Test (10 examples)

```bash
python runner.py \
  --dataset /path/to/spider \
  --limit 10 \
  --verbose
```

### Run Full Dev Set

```bash
python runner.py --dataset /path/to/spider
```

### Custom Backend URL

```bash
python runner.py \
  --dataset /path/to/spider \
  --backend http://localhost:8001 \
  --limit 20
```

### Save Results to Custom Location

```bash
python runner.py \
  --dataset /path/to/spider \
  --output ./results \
  --limit 50
```

## Output

### Console Output

```
============================================================
NL2SQL TEST PIPELINE
============================================================

[1/4] Checking backend...
✓ Backend is running

[2/4] Loading dataset...
✓ Loaded 1034 test cases

[3/4] Executing tests...
[1/1034] concert_singer: Show all concerts that took place in...  ✓ PASS (exact match)
[2/1034] concert_singer: How many distinct types of concert... ~ PARTIAL (exec ok, semantic sim: 0.85)
[3/1034] world_1: Show the names of actors who acted in a mo... ✗ FAIL (Generation error: timeout)
...

[4/4] Generating report...
============================================================
EVALUATION REPORT
============================================================
Total Tests:            1034
Execution Success:      856/1034 (82.8%)
Exact Match (EM):       342/1034 (33.1%)
Result Match:           612/1034 (59.2%)
Avg Semantic Sim:       0.72

Top Errors:
  Timeout: 95
  Syntax error: 42
  Table not found: 28

Results by Database:
  concert_singer       |  55 tests | 87.3% success | 38.2% EM
  pets_and_owners      |  48 tests | 84.2% success | 31.2% EM
  world_1              |  32 tests | 76.5% success | 25.0% EM
...
============================================================

✓ Results saved to: test_results/results_20260430_143022.json
```

### JSON Results File

`test_results/results_YYYYMMDD_HHMMSS.json`:

```json
{
  "timestamp": "20260430_143022",
  "summary": {
    "total_tests": 1034,
    "execution_success_rate": 0.828,
    "exact_match_rate": 0.331,
    "result_match_rate": 0.592,
    "avg_semantic_similarity": 0.72
  },
  "results": [
    {
      "test_id": 0,
      "db_id": "concert_singer",
      "question": "Show all concerts that took place in 2014",
      "expected_sql": "SELECT * FROM concert WHERE YEAR(concert_date) = 2014",
      "generated_sql": "SELECT * FROM concert WHERE YEAR(concert_date) = 2014",
      "execution_success": true,
      "error_message": null,
      "exact_match": true,
      "result_match": true,
      "semantic_match": 1.0
    },
    ...
  ]
}
```

## Metrics Explained

### Execution Accuracy

Percentage of queries that executed without SQL syntax/execution errors.

- **Good baseline**: 70-85% (depends on LLM quality)
- **Target**: > 90%

### Exact Match (EM)

Percentage of generated SQL that exactly matches (after normalization).

- **Spider human performance**: ~80% EM
- **Current SOTA models**: ~40-50% EM
- **Baseline expectation**: 15-30%

### Result Match

Percentage of queries that returned correct results (when executed successfully).

- **Requires**: Correct SQL + correct database state
- **Harder than EM**: Only counts if both execution AND results are correct

### Semantic Similarity

Token-overlap based similarity (0-1) between generated and expected SQL.

- **1.0**: Perfect semantic match
- **>0.8**: Very similar
- **0.5-0.8**: Related but not identical
- **<0.5**: Significantly different approach

## Customization

### Modify Test Limit per DB

Edit `runner.py`, update `get_test_cases()` call:

```python
# Test only first 5 cases per database
test_cases = self.dataset_loader.get_test_cases(limit=5)
```

### Add Custom Metrics

1. Add method to `Metrics` class in `metrics.py`
2. Calculate in `TestExecutor.run_test()`
3. Store in `TestResult` object
4. Report in `AggregateMetrics.print_report()`

Example - Token-level F1 score:

```python
# In metrics.py
@staticmethod
def token_f1(generated_sql: str, expected_sql: str) -> float:
    gen_tokens = set(Metrics._extract_tokens(generated_sql))
    exp_tokens = set(Metrics._extract_tokens(expected_sql))
    # ... calculate F1
```

### Test Different Models

Backend can be pointed at different Ollama models via `main.py`. Try:

```bash
# Run with different model
OLLAMA_MODEL=mistral python main.py

# Then run pipeline
python runner.py --dataset /path/to/spider --limit 20
```

## Next Steps for Full Implementation

1. **Real Result Comparison** — Compare actual query results row-by-row (not just execution success)
2. **Multi-database Support** — Test across PostgreSQL, MySQL, not just SQLite
3. **Error Classification** — Categorize failures by type (syntax, missing table, wrong join, etc.)
4. **Schema Understanding Test** — Isolate schema filtering accuracy
5. **Difficulty Bucketing** — Separate simple vs. complex queries
6. **Parallel Execution** — Use threading/async to run tests in parallel
7. **Performance Tracking** — Monitor latency per query type
8. **Integration Testing** — Test full conversation flow (multi-turn) not just single questions
9. **Automated Regression** — CI/CD pipeline to detect model degradation

## Troubleshooting

### Backend Connection Error

```
❌ Backend health check failed: Connection refused
```

**Solution**: Ensure backend is running on the specified URL:

```bash
cd .. && python main.py
```

### Dataset Not Found

```
FileNotFoundError: Dataset file not found
```

**Solution**: Check dataset path:

```bash
ls -la /path/to/spider/dev.json
```

### Timeout During Tests

```
Execution timeout
```

**Solution**: Increase timeout in `executor.py`:

```python
self.timeout = 60  # Increase to 60 seconds
```

### Out of Memory

If running full Spider (1000+ tests):

```bash
# Run in smaller batches
python runner.py --dataset /path/to/spider --limit 100
python runner.py --dataset /path/to/spider --limit 100 --output results_batch2
```

## Performance Expectations

On a typical machine:

| Operation  | Time        |
| ---------- | ----------- |
| 10 tests   | ~30-60s     |
| 100 tests  | ~5-10 min   |
| 1000 tests | ~50-100 min |

Bottleneck is usually Ollama inference time (~5-15s per query).

## License

Same as main project.
