"""
Main test pipeline runner.
Orchestrates dataset loading, test execution, and metric reporting.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from dataset_loader import DatasetLoader
from metrics import Metrics, TestResult, AggregateMetrics
from executor import BackendClient, TestExecutor


class PipelineRunner:
    """Main orchestrator for test pipeline."""
    
    def __init__(
        self,
        dataset_path: str,
        backend_url: str = "http://localhost:8000",
        output_dir: str = "test_results"
    ):
        """
        Initialize pipeline runner.
        
        Args:
            dataset_path: Path to Spider/Bird dataset
            backend_url: URL of NL2SQL backend
            output_dir: Directory to save results
        """
        self.dataset_loader = DatasetLoader(dataset_path, split="dev")
        self.backend_client = BackendClient(backend_url)
        self.test_executor = TestExecutor(self.backend_client)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.aggregate_metrics = AggregateMetrics()
        self.test_results = []
    
    def run(
        self,
        limit: Optional[int] = None,
        verbose: bool = False,
        fail_fast: bool = False,
        resume_from: Optional[int] = None,
    ) -> None:
        """
        Run full test pipeline.
        
        Args:
            limit: Limit number of tests (for quick runs)
            verbose: Print detailed output
            fail_fast: Stop immediately on first failed test
            resume_from: Resume from a specific test id (inclusive)
        """
        print("\n" + "="*60)
        print("NL2SQL TEST PIPELINE")
        print("="*60)
        
        # Check backend health
        print("\n[1/4] Checking backend...")
        if not self.backend_client.health_check():
            print("❌ Backend not running! Start it with: python main.py")
            return
        print("✓ Backend is running")
        
        # Load dataset
        print("\n[2/4] Loading dataset...")
        test_cases = self.dataset_loader.get_test_cases(limit=limit)

        if resume_from is not None:
            test_cases = [case for case in test_cases if case.get("id", -1) >= resume_from]

        if not test_cases:
            print("❌ No test cases loaded")
            return
        print(f"✓ Loaded {len(test_cases)} test cases")
        if resume_from is not None:
            print(f"✓ Resuming from test id >= {resume_from}")
        
        # Run tests
        print("\n[3/4] Executing tests...")
        for i, test_case in enumerate(test_cases):
            progress = f"[{i+1}/{len(test_cases)}]"
            db_id = test_case["db_id"]
            
            print(f"{progress} {db_id}: {test_case['question'][:50]}...", end="")
            
            # Execute test
            exec_result = self.test_executor.run_test(test_case)
            
            # Build TestResult object
            test_result = TestResult(
                test_id=exec_result["test_id"],
                db_id=exec_result["db_id"],
                question=exec_result["question"]
            )
            
            test_result.expected_sql = exec_result["expected_sql"]
            test_result.generated_sql = exec_result["generated_sql"]
            test_result.generated_result = exec_result.get("generated_result")
            test_result.expected_result = exec_result.get("expected_result")
            test_result.execution_success = exec_result["execution_success"]
            test_result.error_message = exec_result.get("error_message")
            
            # Calculate metrics
            if test_result.generated_sql:
                test_result.exact_match_score = Metrics.exact_match(
                    test_result.generated_sql,
                    test_result.expected_sql
                )
                test_result.semantic_match_score = Metrics.semantic_match(
                    test_result.generated_sql,
                    test_result.expected_sql
                )
                test_result.result_match_score = exec_result.get("result_match", False)
            
            self.aggregate_metrics.add_result(test_result)
            self.test_results.append(test_result)
            
            # Print result indicator
            if test_result.execution_success:
                if test_result.exact_match_score:
                    print(" ✓ PASS (exact match)")
                else:
                    print(f" ~ PARTIAL (exec ok, semantic sim: {test_result.semantic_match_score:.2f})")
            else:
                print(f" ✗ FAIL ({test_result.error_message})")
            
            if verbose and test_result.generated_sql:
                print(f"    Expected: {test_result.expected_sql[:80]}")
                print(f"    Generated: {test_result.generated_sql[:80]}")

            if fail_fast and not test_result.execution_success:
                print("\n⚠ Fail-fast enabled: stopping after first failed test")
                break
        
        # Report results
        print("\n[4/4] Generating report...")
        self.aggregate_metrics.print_report()
        
        # Save detailed results
        self._save_results()
    
    def _save_results(self) -> None:
        """Save detailed test results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.output_dir / f"results_{timestamp}.json"
        
        results_data = {
            "timestamp": timestamp,
            "summary": {
                "total_tests": self.aggregate_metrics.total_tests,
                "execution_success_rate": self.aggregate_metrics.execution_accuracy(),
                "exact_match_rate": self.aggregate_metrics.exact_match_accuracy(),
                "result_match_rate": self.aggregate_metrics.result_match_accuracy(),
                "avg_semantic_similarity": self.aggregate_metrics.avg_semantic_similarity(),
            },
            "results": [r.to_dict() for r in self.test_results],
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"✓ Results saved to: {results_file}")


def main():
    parser = argparse.ArgumentParser(
        description="NL2SQL Test Pipeline for Spider/Bird datasets"
    )
    parser.add_argument(
        "--dataset",
        required=False,
        default=None,
        help="Path to Spider/Bird dataset directory (auto-detects local datasets)"
    )
    parser.add_argument(
        "--backend",
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of tests (for quick runs)"
    )
    parser.add_argument(
        "--output",
        default="test_results",
        help="Output directory for results (default: test_results)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed output"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on first failed test"
    )
    parser.add_argument(
        "--resume-from",
        type=int,
        default=None,
        help="Resume from this test id (inclusive)"
    )
    
    args = parser.parse_args()
    
    # Auto-detect local dataset if not specified
    dataset_path = args.dataset
    if not dataset_path:
        # Check for local dataset
        test_pipeline_dir = Path.cwd()
        possible_names = ["spider_data", "spider", "bird_data", "bird", "datasets", "data"]
        
        for name in possible_names:
            candidate = test_pipeline_dir / name
            if candidate.exists() and (candidate / "dev.json").exists():
                dataset_path = str(candidate)
                print(f"✓ Auto-detected local dataset: {name}")
                break
        
        if not dataset_path:
            print("❌ Dataset not specified and no local dataset found")
            print("\nUsage:")
            print("  python runner.py --dataset /path/to/spider")
            print("  python runner.py --dataset ./spider_data")
            print("  python runner.py  # Auto-detect local dataset")
            sys.exit(1)
    else:
        # Expand user path and handle relative paths
        dataset_path = os.path.expanduser(dataset_path)
        if not os.path.isabs(dataset_path):
            dataset_path = str(Path.cwd() / dataset_path)
    
    runner = PipelineRunner(
        dataset_path=dataset_path,
        backend_url=args.backend,
        output_dir=args.output
    )
    
    runner.run(
        limit=args.limit,
        verbose=args.verbose,
        fail_fast=args.fail_fast,
        resume_from=args.resume_from,
    )


if __name__ == "__main__":
    main()
