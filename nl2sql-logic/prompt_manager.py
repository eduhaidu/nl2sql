import ollama
import json

class PromptManager:
    def __init__(self, nl_input="", model_name='nl2sql', temperature=0.7, max_tokens=512, schema=None):
        self.nl_input = nl_input
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.schema = schema
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
            "4. Return only the SQL query without any additional text.\n"
        )
        context_prompt += "\n" + rules_prompt
        if self.schema:
            context_prompt += f" The database schema is as follows: {self.format_schema_for_prompt()}"
        self.conversation_history.append({"role": "system", "content": context_prompt})

    def format_schema_for_prompt(self):
        if not self.schema:
            return "No schema information available."
        schema_str = "Database Schema:\n"
        for table, columns in self.schema.items():
            schema_str += f"Table: {table}\n"
            for column in columns:
                if isinstance(column, dict) and 'foreign_keys' in column:
                    for fk in column['foreign_keys']:
                        schema_str += f"  Foreign Key: {fk['column']} references {fk['references']}\n"
                else:
                    schema_str += f"  Column: {column['name']}, Type: {column['type']}, Nullable: {column['nullable']}, Primary Key: {column['primary_key']}\n"
        return schema_str

    def generate_prompt(self, nl_input):
        prompt = f"Question: {nl_input}\nSQL:"
        return prompt
    
    def filter_relevant_tables(self, schema_info, nl_input):
        #TODO: Implement relevance filtering based on nl_input
        return schema_info
        

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