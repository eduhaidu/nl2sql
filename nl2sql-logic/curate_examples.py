"""
Script to curate high-quality few-shot examples from BIRD and Spider datasets
"""
import json
import random
import re
from pathlib import Path

def extract_schema_from_sql(sql):
    """Extract a minimal schema from SQL query showing tables and columns used"""
    # Clean backticks and normalize
    sql_clean = sql.replace('`', '')
    
    # Extract table names with aliases
    from_pattern = r'\bFROM\s+(\[?\w+\]?)\s+(?:AS\s+)?(\w+)?'
    join_pattern = r'\b(?:INNER\s+|LEFT\s+|RIGHT\s+|OUTER\s+)?JOIN\s+(\[?\w+\]?)\s+(?:AS\s+)?(\w+)?'
    
    tables = {}  # alias -> table_name
    
    # Find all FROM clauses
    for match in re.finditer(from_pattern, sql_clean, re.IGNORECASE):
        table_name = match.group(1)
        alias = match.group(2) if match.group(2) else table_name[0]  # Use first letter as alias if none
        tables[alias] = table_name
    
    # Find all JOIN clauses
    for match in re.finditer(join_pattern, sql_clean, re.IGNORECASE):
        table_name = match.group(1)
        alias = match.group(2) if match.group(2) else table_name[0]
        tables[alias] = table_name
    
    # Extract columns for each table
    table_columns = {table: set() for table in tables.values()}
    
    # Pattern to match alias.column or table.column (but not functions/keywords)
    # Match word.word or word.[word with special chars]
    column_pattern = r'\b(\w+)\.((?:\[[\w\s\(\)%\-/]+\])|(?:\w+))\b'
    
    for match in re.finditer(column_pattern, sql):
        alias_or_table = match.group(1)
        column = match.group(2).strip()
        
        # Skip SQL keywords and functions
        if alias_or_table.upper() in ['SELECT', 'FROM', 'WHERE', 'HAVING', 'ORDER', 'GROUP', 'AS', 'ON']:
            continue
        
        # Map alias to table name
        if alias_or_table in tables:
            table_name = tables[alias_or_table]
            # Clean column name
            column_clean = column.strip('[]')
            # Skip if it looks like a subquery or function result
            if not any(kw in column_clean.upper() for kw in ['SELECT', 'CASE', 'CAST']):
                table_columns[table_name].add(column)
    
    # Format as minimal schema
    if not table_columns or all(len(cols) == 0 for cols in table_columns.values()):
        return "Schema: " + ", ".join(tables.values())
    
    schema_parts = []
    for table_name, columns in table_columns.items():
        if columns:
            cols_str = ", ".join(sorted(columns)[:5])  # Limit to 5 columns
            if len(columns) > 5:
                cols_str += ", ..."
            schema_parts.append(f"{table_name}({cols_str})")
        else:
            schema_parts.append(table_name)
    
    return "Tables: " + ", ".join(schema_parts)

def load_bird_examples(bird_path, num_examples=15):
    """Load diverse examples from BIRD dataset"""
    with open(bird_path, 'r') as f:
        data = json.load(f)
    
    # Categorize by difficulty and features
    simple = []
    moderate = []
    challenging = []
    
    for item in data:
        example = {
            "source": "BIRD",
            "db_id": item['db_id'],
            "question": item['question'],
            "sql": item['SQL'],
            "difficulty": item.get('difficulty', 'unknown')
        }
        
        if item.get('difficulty') == 'simple':
            simple.append(example)
        elif item.get('difficulty') == 'moderate':
            moderate.append(example)
        elif item.get('difficulty') == 'challenging':
            challenging.append(example)
    
    # Select diverse examples
    selected = []
    selected.extend(random.sample(simple[:100], min(5, len(simple))))  # 5 simple
    selected.extend(random.sample(moderate[:100], min(7, len(moderate))))  # 7 moderate
    selected.extend(random.sample(challenging[:100], min(3, len(challenging))))  # 3 challenging
    
    return selected[:num_examples]

def add_query_patterns(examples):
    """Categorize examples by SQL pattern for better selection"""
    patterns = {
        'basic_select': [],
        'join': [],
        'aggregation': [],
        'subquery': [],
        'special_chars': [],
        'complex': []
    }
    
    for ex in examples:
        sql = ex['sql'].upper()
        
        if 'JOIN' in sql:
            patterns['join'].append(ex)
        if any(agg in sql for agg in ['SUM(', 'COUNT(', 'AVG(', 'MAX(', 'MIN(', 'GROUP BY']):
            patterns['aggregation'].append(ex)
        if 'SELECT' in sql and sql.count('SELECT') > 1:
            patterns['subquery'].append(ex)
        if any(char in ex['sql'] for char in ['[', '(', ')', '%']):
            patterns['special_chars'].append(ex)
        if len(sql.split()) > 20:  # Complex queries
            patterns['complex'].append(ex)
        if 'WHERE' in sql and 'JOIN' not in sql and 'GROUP BY' not in sql:
            patterns['basic_select'].append(ex)
    
    return patterns

def create_balanced_examples(bird_path, output_path, total_examples=20):
    """Create a balanced set of examples covering different patterns"""
    print(f"Loading BIRD examples from {bird_path}...")
    bird_examples = load_bird_examples(bird_path, num_examples=25)
    
    print(f"Loaded {len(bird_examples)} BIRD examples")
    
    # Categorize by pattern
    patterns = add_query_patterns(bird_examples)
    
    print("\nExamples by pattern:")
    for pattern, exs in patterns.items():
        print(f"  {pattern}: {len(exs)}")
    
    # Select balanced set
    selected = []
    
    # Ensure we have at least one of each pattern
    for pattern, exs in patterns.items():
        if exs:
            selected.append(random.choice(exs))
    
    # Fill remaining slots with diverse examples
    remaining = [ex for ex in bird_examples if ex not in selected]
    selected.extend(random.sample(remaining, min(total_examples - len(selected), len(remaining))))
    
    # Format for prompt_examples.json
    formatted_examples = []
    for ex in selected[:total_examples]:
        # Extract minimal schema from SQL
        schema = extract_schema_from_sql(ex['sql'])
        
        formatted_examples.append({
            "source": ex.get('source', 'BIRD'),
            "db_id": ex.get('db_id', ''),
            "schema": schema,
            "question": ex['question'],
            "sql": ex['sql'],
            "difficulty": ex.get('difficulty', 'unknown')
        })
    
    # Save to file
    with open(output_path, 'w') as f:
        json.dump(formatted_examples, f, indent=2)
    
    print(f"\n✓ Created {len(formatted_examples)} examples in {output_path}")
    print("\nExample breakdown:")
    difficulties = {}
    for ex in formatted_examples:
        diff = ex.get('difficulty', 'unknown')
        difficulties[diff] = difficulties.get(diff, 0) + 1
    for diff, count in difficulties.items():
        print(f"  {diff}: {count}")
    
    return formatted_examples

def download_spider_examples():
    """Download Spider dataset examples"""
    print("\nTo add Spider examples:")
    print("1. Visit: https://yale-lily.github.io/spider")
    print("2. Download the dataset")
    print("3. Extract train_spider.json")
    print("4. Run: python curate_examples.py --spider path/to/train_spider.json")
    print("\nFor now, using BIRD examples only.")

if __name__ == "__main__":
    import sys
    
    # Paths
    bird_path = Path("../dev_20240627/dev.json")
    output_path = Path("prompt_examples.json")
    
    if not bird_path.exists():
        print(f"Error: BIRD dataset not found at {bird_path}")
        print("Please update the bird_path variable with the correct path")
        sys.exit(1)
    
    # Create curated examples
    examples = create_balanced_examples(bird_path, output_path, total_examples=20)
    
    print("\n" + "="*60)
    print("Sample examples:")
    print("="*60)
    for i, ex in enumerate(examples[:3], 1):
        print(f"\n{i}. Question: {ex['question'][:70]}...")
        print(f"   Schema: {ex.get('schema', 'N/A')[:80]}...")
        print(f"   SQL: {ex['sql'][:80]}...")
        print(f"   Difficulty: {ex['difficulty']}")
    
    print("\n" + "="*60)
    print("✓ Examples curated successfully!")
    print("="*60)
