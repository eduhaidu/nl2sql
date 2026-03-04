import json
import os
from datetime import datetime

class ExampleManager:
    def __init__(self, static_file='prompt_examples.json', production_file='production_examples.json'):
        self.static_file = static_file
        self.production_file = production_file
        self.static_examples = []
        self.production_examples = []
        
        # Load both static and production examples
        self.load_examples_from_file(self.static_file, 'static')
        self.load_examples_from_file(self.production_file, 'production')

    def add_example(self, question, sql, source='static'):
        """Add example to appropriate pool based on source"""
        example = {
            "question": question,
            "sql": sql,
            "source": source,
            "added_at": datetime.now().isoformat()
        }
        
        if source == 'production':
            # Check for duplicates in production examples
            for existing in self.production_examples:
                if existing['question'] == question and existing['sql'] == sql:
                    return  # Skip duplicates
            
            self.production_examples.append(example)
            self.save_examples_to_file(self.production_file, self.production_examples)
        else:
            self.static_examples.append(example)
            self.save_examples_to_file(self.static_file, self.static_examples)

    def add_production_example(self, question, sql):
        """Convenience method to add successful production queries"""
        self.add_example(question, sql, source='production')

    def add_corrected_example(self, question, generated_sql, corrected_sql):
        """Add a corrected query as a production example"""
        example = {
            "question": question,
            "sql": corrected_sql,  # Use the corrected SQL
            "original_sql": generated_sql,
            "source": "production",
            "corrected": True,
            "added_at": datetime.now().isoformat()
        }
        
        # Check for duplicates
        for existing in self.production_examples:
            if existing['question'] == question and existing['sql'] == corrected_sql:
                return
        
        self.production_examples.append(example)
        self.save_examples_to_file(self.production_file, self.production_examples)

    def get_all_examples(self):
        """Get all examples (static + production)"""
        return self.static_examples + self.production_examples
    
    def get_static_examples(self):
        """Get only static examples"""
        return self.static_examples
    
    def get_production_examples(self):
        """Get only production examples"""
        return self.production_examples

    def get_examples(self):
        """Alias for get_all_examples for backward compatibility"""
        return self.get_all_examples()
    
    def load_examples_from_file(self, file_path, source='static'):
        """Load examples from a JSON file"""
        if not os.path.exists(file_path):
            print(f"File {file_path} not found, starting with empty {source} examples")
            return
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            for item in data:
                example = {
                    "question": item['question'],
                    "sql": item['sql'],
                    "source": item.get('source', source),
                    "added_at": item.get('added_at', None),
                    "corrected": item.get('corrected', False),
                    "original_sql": item.get('original_sql', None)
                }
                
                if source == 'production':
                    self.production_examples.append(example)
                else:
                    self.static_examples.append(example)
            
            print(f"Loaded {len(data)} examples from {file_path}")
        except Exception as e:
            print(f"Error loading examples from {file_path}: {e}")

    def save_examples_to_file(self, file_path, examples):
        """Save examples to a JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(examples, f, indent=4)
            print(f"Saved {len(examples)} examples to {file_path}")
        except Exception as e:
            print(f"Error saving examples to {file_path}: {e}")