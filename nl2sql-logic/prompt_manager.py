import ollama
import json
from sentence_transformers import SentenceTransformer, util

class PromptManager:
    def __init__(self, nl_input="", model_name='nl2sql', schema=None, database_type='sqlite'):
        self.nl_input = nl_input
        self.model_name = model_name
        self.schema = schema
        self.database_type = database_type
        self.client = ollama.Client()
        self.examples = json.loads(open('prompt_examples.json').read())
        self.conversation_history = []
        self._initialize_context()

    def _initialize_context(self):
        context_prompt = "You are an SQL expert that translates natural language to SQL queries."
        rules_prompt = (
            "Follow these rules when generating SQL queries:\n"
            "1. Only use tables and columns that exist in the provided database schema.\n"
            "2. Ensure SQL syntax is correct and compatible with the target database.\n"
            "3. Optimize queries for performance where possible.\n"
            "4. Return only the SQL query without any additional text, explanations or formatting.\n"
            "5. Handle table and column names with spaces or special characters by enclosing them in square brackets or double quotes.\n"
        )
        context_prompt += "\n" + rules_prompt
        if self.database_type:
            db_prompt = f"The target database type is {self.database_type}. Ensure the SQL syntax is compatible with this database."
            context_prompt += "\n" + db_prompt
        # if self.schema:
        #     schema_prompt = "Here is the database schema information:\n" + self.format_schema_to_json()
        #     context_prompt += "\n" + schema_prompt
        self.conversation_history.append({"role": "system", "content": context_prompt})

    def filter_relevant_tables(self, nl_input):
        model = SentenceTransformer('all-MiniLM-L6-v2')
        nl_embedding = model.encode(nl_input, convert_to_tensor=True)

        relevant_tables = {}
        for table_name, columns in self.schema.items():
            column_names = [col['name'] for col in columns if 'name' in col]
            table_text = table_name + ' ' + ' '.join(column_names)
            table_embedding = model.encode(table_text, convert_to_tensor=True)

            similarity = util.pytorch_cos_sim(nl_embedding, table_embedding).item()
            if similarity > 0.3:  # Threshold can be adjusted
                relevant_tables[table_name] = columns
        return relevant_tables

    def format_schema_to_json(self):
        return json.dumps(self.schema, indent=4)
    
    def needs_escape(self, name):
        """Check if column/table name needs escaping"""
        import re
        return bool(re.search(r'[\s\(\)%\-/\#@\$]', name)) or (name and name[0].isdigit())
    
    def format_filtered_schema(self, filtered_schema):
        """Format filtered schema with escaped column names"""
        formatted = ""
        for table_name, columns in filtered_schema.items():
            table_display = f"[{table_name}]" if self.needs_escape(table_name) else table_name
            formatted += f"Table: {table_display}\n"
            for column in columns:
                if 'name' in column:
                    col_name = column['name']
                    col_display = f"[{col_name}]" if self.needs_escape(col_name) else col_name
                    formatted += f"  Column: {col_display}, Type: {column.get('type', 'UNKNOWN')}\n"
            formatted += "\n"
        return formatted.strip()

    def generate_prompt(self, nl_input):
        filtered_tables = self.filter_relevant_tables(nl_input)
        formatted_schema = self.format_filtered_schema(filtered_tables)
        prompt = f"Question: {nl_input}\n\nSchema (columns in [brackets] require quoting in SQL):\n{formatted_schema}\n\nGenerate the SQL query that answers the question based on the provided schema."
        return prompt
        
    def get_response(self, nl_input):
        self.nl_input = nl_input
        prompt = self.generate_prompt(nl_input)
        self.conversation_history.append({"role": "user", "content": prompt})

        response = self.client.chat(
            model=self.model_name,
            messages=self.conversation_history
            # temperature=self.temperature,
            # max_tokens=self.max_tokens
        )

        self.conversation_history.append({"role": "assistant", "content": response.message['content']})
        return response.message['content']