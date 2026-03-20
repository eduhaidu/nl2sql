import ollama
import json
import re
from example_manager import ExampleManager
from sentence_transformers import SentenceTransformer, util

class PromptManager:
    def __init__(self, nl_input="", model_name='nl2sql', schema=None, database_type='sqlite'):
        self.nl_input = nl_input
        self.model_name = model_name
        self.schema = schema
        self.database_type = database_type
        self.client = ollama.Client()
        self.example_manager = ExampleManager()
        self.examples = self.example_manager.get_examples()
        self.conversation_history = []
        self.max_history_turns = 3  # Keep last 3 Q&A pairs
        self._initialize_context()
        self.initialize_sentence_transformer()

    def _initialize_context(self):
        context_prompt = "You are an SQL expert that translates natural language to SQL queries."
        rules_prompt = (
            "Follow these rules when generating SQL queries:\n"
            "1. Only use tables and columns that exist in the provided database schema.\n"
            "2. Ensure SQL syntax is correct and compatible with the target database.\n"
            "3. Optimize queries for performance where possible.\n"
            "4. Return ONLY ONE final SQL query that directly answers the question. Do not provide multiple query options, intermediate queries, or step-by-step alternatives.\n"
            "5. Do not include ANY explanations, descriptions, notes, or commentary - ONLY the SQL query itself.\n"
            "6. Handle table and column names with spaces or special characters by enclosing them in square brackets or double quotes.\n"
            "7. Always answer ONLY the latest user question in the current turn.\n"
            "8. If the required table/column is missing from schema context, return the safest valid SQL based only on provided schema.\n"
            "9. Your entire response should be executable SQL - nothing else.\n"
        )
        context_prompt += "\n" + rules_prompt
        if self.database_type:
            db_prompt = f"The target database type is {self.database_type}. Ensure the SQL syntax is compatible with this database."
            context_prompt += "\n" + db_prompt
        # if self.schema:
        #     schema_prompt = "Here is the database schema information:\n" + self.format_schema_to_json()
        #     context_prompt += "\n" + schema_prompt
        self.system_prompt = {"role": "system", "content": context_prompt}
        self.conversation_history.append(self.system_prompt)

    def initialize_sentence_transformer(self):
        """Initialize the sentence transformer model for semantic search"""
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def filter_relevant_tables(self, nl_input):
        # Safety check: ensure schema is a dictionary
        if not isinstance(self.schema, dict) or not self.schema:
            return {}
            
        model = self.model if hasattr(self, 'model') else SentenceTransformer('all-MiniLM-L6-v2')
        nl_embedding = model.encode(nl_input, convert_to_tensor=True)

        relevant_tables = {}
        for table_name, table_data in self.schema.items():
            # Handle new schema structure: {'description': ..., 'columns': [...]}
            if isinstance(table_data, dict) and 'columns' in table_data:
                columns = table_data['columns']
                table_description = table_data.get('description', '')
            else:
                # Handle old schema structure: [columns_list]
                columns = table_data
                table_description = ''
            
            column_names = [col['name'] for col in columns if 'name' in col]
            table_text = table_name + ' ' + ' '.join(column_names)
            
            # Add table description to semantic search
            if table_description:
                table_text += ' ' + table_description
            
            # Add column descriptions to semantic search
            for col in columns:
                if 'name' in col and 'description' in col:
                    table_text += ' ' + col['description']
            
            table_embedding = model.encode(table_text, convert_to_tensor=True)

            similarity = util.pytorch_cos_sim(nl_embedding, table_embedding).item()
            if similarity > 0.5:  # Threshold can be adjusted
                relevant_tables[table_name] = table_data
        return relevant_tables
    
    
    def select_relevant_static_examples(self, nl_input, example_count=2):
        model = self.model if hasattr(self, 'model') else SentenceTransformer('all-MiniLM-L6-v2')
        nl_embedding = model.encode(nl_input, convert_to_tensor=True)

        example_similarities = []
        for example in self.examples:
            example_text = example['question'] + ' ' + example['sql']
            example_embedding = model.encode(example_text, convert_to_tensor=True)
            similarity = util.pytorch_cos_sim(nl_embedding, example_embedding).item()
            example_similarities.append((similarity, example))

        example_similarities.sort(key=lambda x: x[0], reverse=True)
        selected_examples = [ex for _, ex in example_similarities[:example_count]]
        return selected_examples
    
    def select_relevant_examples(self, nl_input, example_count=3, 
                                 production_ratio=0.6, 
                                 diversity_threshold=0.85):
        """
        Intelligently combine static examples with production examples from JSON.
        
        Args:
            nl_input: The user's natural language query
            example_count: Total number of examples to return
            production_ratio: Proportion of examples from production (0.0-1.0)
            diversity_threshold: Similarity threshold to ensure diverse examples (0.0-1.0)
        
        Returns:
            List of selected examples with best semantic match
        """
        model = self.model if hasattr(self, 'model') else SentenceTransformer('all-MiniLM-L6-v2')
        nl_embedding = model.encode(nl_input, convert_to_tensor=True)
        
        # Get examples from both pools
        static_examples = self.example_manager.get_static_examples()
        production_examples = self.example_manager.get_production_examples()
        
        # Calculate target counts
        production_count = int(example_count * production_ratio)
        static_count = example_count - production_count
        
        # If no production examples, use all static
        if not production_examples:
            production_count = 0
            static_count = example_count
        
        # Calculate similarities for production examples
        production_similarities = []
        for example in production_examples:
            example_text = example['question'] + ' ' + example['sql']
            example_embedding = model.encode(example_text, convert_to_tensor=True)
            similarity = util.pytorch_cos_sim(nl_embedding, example_embedding).item()
            production_similarities.append((similarity, example))
        
        # Calculate similarities for static examples
        static_similarities = []
        for example in static_examples:
            example_text = example['question'] + ' ' + example['sql']
            example_embedding = model.encode(example_text, convert_to_tensor=True)
            similarity = util.pytorch_cos_sim(nl_embedding, example_embedding).item()
            static_similarities.append((similarity, example))
        
        # Sort by similarity
        production_similarities.sort(key=lambda x: x[0], reverse=True)
        static_similarities.sort(key=lambda x: x[0], reverse=True)
        
        selected_examples = []
        selected_embeddings = []
        
        # Select production examples with diversity check
        for sim, example in production_similarities:
            if len([e for e in selected_examples if e.get('source') == 'production']) >= production_count:
                break
            
            # Check diversity - avoid very similar examples
            example_text = example['question'] + ' ' + example['sql']
            example_embedding = model.encode(example_text, convert_to_tensor=True)
            
            is_diverse = True
            for selected_emb in selected_embeddings:
                similarity_to_selected = util.pytorch_cos_sim(example_embedding, selected_emb).item()
                if similarity_to_selected > diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                selected_examples.append(example)
                selected_embeddings.append(example_embedding)
        
        # Fill remaining with static examples (also with diversity check)
        for sim, example in static_similarities:
            if len([e for e in selected_examples if e.get('source') != 'production']) >= static_count:
                break
            
            example_text = example['question'] + ' ' + example['sql']
            example_embedding = model.encode(example_text, convert_to_tensor=True)
            
            is_diverse = True
            for selected_emb in selected_embeddings:
                similarity_to_selected = util.pytorch_cos_sim(example_embedding, selected_emb).item()
                if similarity_to_selected > diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                selected_examples.append(example)
                selected_embeddings.append(example_embedding)
        
        # If we still don't have enough examples (due to diversity filtering),
        # relax diversity and add top-ranked remaining examples
        if len(selected_examples) < example_count:
            all_remaining = [(s, e) for s, e in production_similarities + static_similarities
                           if e not in selected_examples]
            all_remaining.sort(key=lambda x: x[0], reverse=True)
            
            for sim, example in all_remaining:
                if len(selected_examples) >= example_count:
                    break
                selected_examples.append(example)
        
        # Log what we selected
        production_selected = sum(1 for e in selected_examples if e.get('source') == 'production')
        static_selected = len(selected_examples) - production_selected
        print(f"Selected {len(selected_examples)} examples: "
              f"{production_selected} from production, {static_selected} from static")
        
        return selected_examples
    
    def select_examples_from_history(self, nl_input, history_tuples, example_count=2):
        model = self.model if hasattr(self, 'model') else SentenceTransformer('all-MiniLM-L6-v2')
        nl_embedding = model.encode(nl_input, convert_to_tensor=True)

        example_similarities = []
        for message, sender, timestamp in history_tuples:
            if sender == "user":
                example_text = message
            else:
                example_text = "Assistant response: " + message
            
            example_embedding = model.encode(example_text, convert_to_tensor=True)
            similarity = util.pytorch_cos_sim(nl_embedding, example_embedding).item()
            example_similarities.append((similarity, {"message": message, "sender": sender}))

        example_similarities.sort(key=lambda x: x[0], reverse=True)
        selected_examples = [ex for _, ex in example_similarities[:example_count]]
        return selected_examples
    
    def format_schema_to_json(self):
        return json.dumps(self.schema, indent=4)
    
    def needs_escape(self, name):
        """Check if column/table name needs escaping"""
        import re
        return bool(re.search(r'[\s\(\)%\-/\#@\$]', name)) or (name and name[0].isdigit())
    
    def format_filtered_schema(self, filtered_schema):
        """Format filtered schema with escaped column names and descriptions"""
        formatted = ""
        for table_name, table_data in filtered_schema.items():
            table_display = f"[{table_name}]" if self.needs_escape(table_name) else table_name
            
            # Handle new schema structure: {'description': ..., 'columns': [...]}
            if isinstance(table_data, dict) and 'columns' in table_data:
                columns = table_data['columns']
                table_description = table_data.get('description', '')
                if table_description:
                    formatted += f"Table: {table_display} - {table_description}\n"
                else:
                    formatted += f"Table: {table_display}\n"
            else:
                # Handle old schema structure: [columns_list]
                columns = table_data
                formatted += f"Table: {table_display}\n"
            
            for column in columns:
                if 'name' in column:
                    col_name = column['name']
                    col_display = f"[{col_name}]" if self.needs_escape(col_name) else col_name
                    col_type = column.get('type', 'UNKNOWN')
                    col_desc = column.get('description', '')
                    
                    if col_desc:
                        formatted += f"  Column: {col_display}, Type: {col_type} - {col_desc}\n"
                    else:
                        formatted += f"  Column: {col_display}, Type: {col_type}\n"
            formatted += "\n"
        return formatted.strip()

    def generate_prompt(self, nl_input):
        filtered_schema = self.filter_relevant_tables(nl_input)
        if not filtered_schema and isinstance(self.schema, dict):
            # Fallback: provide a small schema slice even when semantic matching is weak
            fallback_items = list(self.schema.items())[:5]
            filtered_schema = dict(fallback_items)
        formatted_schema = self.format_filtered_schema(filtered_schema)
        prompt = f"Question: {nl_input}\n\nSchema (columns in [brackets] require quoting in SQL):\n{formatted_schema}\n\n"

        examples = self.select_relevant_examples(nl_input)
        if examples:
            prompt += "Examples:\n"
            for example in examples:
                prompt += f"Question: {example['question']}\nSQL: {example['sql']}\n\n"

        # Strong closing instruction
        prompt += "Generate ONLY the SQL query - no explanations, no alternatives, no text. Just executable SQL:"
        return prompt
        
    def trim_conversation_history(self):
        """Keep only system prompt + last N Q&A turns to prevent context overflow"""
        if len(self.conversation_history) > (1 + self.max_history_turns * 2):
            # Keep system prompt (index 0) + last N user/assistant pairs
            self.conversation_history = [self.system_prompt] + self.conversation_history[-(self.max_history_turns * 2):]
    
    def reset_conversation(self):
        """Reset conversation history to just the system prompt"""
        self.conversation_history = [self.system_prompt]

    def _compact_assistant_message(self, assistant_text):
        """Keep assistant memory compact by storing SQL only when possible."""
        if not assistant_text:
            return assistant_text

        code_block_pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(code_block_pattern, assistant_text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        select_match = re.search(r"(SELECT[\s\S]*?;)", assistant_text, re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()

        return assistant_text.strip()

    def _build_request_messages(self, nl_input):
        """Build transient request messages: compact memory + fresh schema/examples."""
        prompt = self.generate_prompt(nl_input)

        compact_history = self.conversation_history[1:] if len(self.conversation_history) > 1 else []
        max_items = self.max_history_turns * 2
        if len(compact_history) > max_items:
            compact_history = compact_history[-max_items:]

        return [self.system_prompt] + compact_history + [{"role": "user", "content": prompt}]
    
    def load_conversation_history(self, history_tuples):
        """Load conversation history from PostgreSQL format [(message, sender, timestamp), ...]"""
        self.conversation_history = [self.system_prompt]  # Reset to system prompt
        
        for message, sender, timestamp in history_tuples:
            role = "user" if sender == "user" else "assistant"
            if role == "assistant":
                message = self._compact_assistant_message(message)
            self.conversation_history.append({"role": role, "content": message})
        
        # Trim if needed
        self.trim_conversation_history()
        print(f"Loaded {len(history_tuples)} messages into conversation history")
        
    def get_response(self, nl_input):
        self.nl_input = nl_input
        request_messages = self._build_request_messages(nl_input)

        response = self.client.chat(
            model=self.model_name,
            messages=request_messages,
            # temperature=self.temperature,
            # max_tokens=self.max_tokens
        )

        assistant_text = response.message['content']
        compact_assistant = self._compact_assistant_message(assistant_text)

        # Persist compact memory only; request-specific schema/examples are transient
        self.conversation_history.append({"role": "user", "content": nl_input})
        self.conversation_history.append({"role": "assistant", "content": compact_assistant})
        self.trim_conversation_history()
        return assistant_text