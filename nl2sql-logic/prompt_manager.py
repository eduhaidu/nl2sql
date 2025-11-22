import ollama

class PromptManager:
    def __init__(self, nl_input="", model_name='nl2sql', temperature=0.7, max_tokens=512, schema=None):
        self.nl_input = nl_input
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.schema = schema
        self.client = ollama.Client()

    def generate_prompt(self, nl_input):
        prompt = f"User: {nl_input}\nAI:"
        if self.schema:
            prompt = f"Schema: {self.schema}\n" + prompt
        return prompt
    
    #Function to extract only relevant schema parts
    def filter_schema(self, data):
        if not self.schema:
            return data
        filtered_data = {key: data[key] for key in self.schema if key in data}
        return filtered_data

    def get_response(self, nl_input):
        prompt = self.generate_prompt(nl_input)
        response = self.client.generate(
            model = self.model_name,
            prompt = prompt
        )
        return response