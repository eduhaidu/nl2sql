"""
Quick start guide and validation script for test pipeline.
"""

import sys
import os
from pathlib import Path


def print_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")


def check_dependencies():
    """Check if required packages are installed."""
    print_section("Checking Dependencies")
    
    required_packages = ['requests']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\nInstall missing packages:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def check_backend():
    """Check if backend is running."""
    print_section("Checking Backend")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running at http://localhost:8000")
            return True
        else:
            print(f"✗ Backend returned status {response.status_code}")
    except Exception as e:
        print(f"✗ Backend not running: {e}")
        print(f"\nStart backend with:")
        print(f"  cd .. && python main.py")
    
    return False


def check_dataset(dataset_path):
    """Check if dataset files exist."""
    print_section("Checking Dataset")
    
    dataset_path = Path(dataset_path)
    required_files = ["dev.json", "tables.json"]  # train.json is optional
    optional_files = ["train.json"]
    missing_required = []
    
    for filename in required_files:
        file_path = dataset_path / filename
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024**2)
            print(f"✓ {filename} ({size_mb:.1f} MB)")
        else:
            print(f"✗ {filename} (missing)")
            missing_required.append(filename)
    
    # Check optional files
    for filename in optional_files:
        file_path = dataset_path / filename
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024**2)
            print(f"✓ {filename} (optional, {size_mb:.1f} MB)")
        else:
            print(f"• {filename} (optional, not present)")
    
    if missing_required:
        print(f"\nDataset incomplete at: {dataset_path}")
        print(f"Missing required files: {', '.join(missing_required)}")
        print(f"Download Spider from: https://yale-lily.github.io/spider")
        return False
    
    return True


def run_quick_test():
    """Run a quick test to validate everything works."""
    print_section("Running Quick Validation Test")
    
    try:
        from metrics import Metrics, TestResult, AggregateMetrics
        
        # Test metrics
        expected = "SELECT * FROM users"
        generated = "select * from users"
        
        exact = Metrics.exact_match(expected, generated)
        semantic = Metrics.semantic_match(expected, generated)
        
        print(f"✓ Metrics working")
        print(f"  - Exact match: {exact}")
        print(f"  - Semantic similarity: {semantic:.2f}")
        
        # Test TestResult
        result = TestResult(0, "test_db", "test question")
        result.expected_sql = expected
        result.generated_sql = generated
        result.execution_success = True
        result.exact_match_score = exact
        result.semantic_match_score = semantic
        
        print(f"✓ TestResult object created")
        
        # Test AggregateMetrics
        agg = AggregateMetrics()
        agg.add_result(result)
        
        print(f"✓ AggregateMetrics working")
        print(f"  - Execution accuracy: {agg.execution_accuracy():.1%}")
        print(f"  - Exact match accuracy: {agg.exact_match_accuracy():.1%}")
        
        return True
    
    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        return False


def show_next_steps():
    """Show next steps for user."""
    print_section("Next Steps")
    
    print("""
1. Prepare your environment:
   cd test_pipeline
   pip install -r requirements.txt

2. Start the backend (in another terminal):
   cd ..
   python main.py

3. Run a quick test (10 examples):
   python runner.py --dataset /path/to/spider --limit 10 -v

4. Run full evaluation:
   python runner.py --dataset /path/to/spider

5. Check results:
   cat test_results/results_*.json | head -50

For more details, see README.md
    """)


def find_local_dataset():
    """Check for dataset in current directory or subdirectories."""
    test_pipeline_dir = Path.cwd()
    
    # Check for common dataset folder names
    possible_names = [
        "spider_data",
        "spider",
        "bird_data",
        "bird",
        "datasets",
        "data"
    ]
    
    for name in possible_names:
        dataset_path = test_pipeline_dir / name
        if dataset_path.exists() and (dataset_path / "dev.json").exists():
            print(f"✓ Found local dataset: ./{name}")
            return str(dataset_path)
    
    return None


def main():
    """Main validation flow."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         NL2SQL Test Pipeline - Setup Validator            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Fix dependencies first")
        return False
    
    # Check backend (optional for now)
    backend_ok = check_backend()
    if not backend_ok:
        print("\n⚠  Backend not running (will be needed to run tests)")
    
    # Check for local dataset first
    print_section("Checking for Local Dataset")
    local_dataset = find_local_dataset()
    
    if local_dataset:
        dataset_path = local_dataset
        print(f"Using local dataset: {dataset_path}")
    else:
        print("No local dataset found")
        # Ask user for dataset path
        dataset_path = input("\n📁 Enter path to Spider dataset (default: ~/spider): ").strip()
        if not dataset_path:
            dataset_path = os.path.expanduser("~/spider")
        elif not dataset_path.startswith("/"):
            # Support relative paths
            dataset_path = (Path.cwd() / dataset_path).resolve()
    
    dataset_path = os.path.expanduser(dataset_path)  # Expand ~ if used
    
    if not Path(dataset_path).exists():
        print(f"❌ Dataset path not found: {dataset_path}")
        return False
    
    if not check_dataset(dataset_path):
        print("\n❌ Fix dataset issues first")
        return False
    
    # Run validation
    if not run_quick_test():
        print("\n❌ Validation test failed")
        return False
    
    # Show next steps
    show_next_steps()
    
    print("\n✅ Setup validation complete!")
    print("   You're ready to run the test pipeline.\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
