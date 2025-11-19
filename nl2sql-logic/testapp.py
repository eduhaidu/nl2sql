from prompt_manager import PromptManager
from schema_processor import SchemaProcessor

def main():
    # Initialize Schema Processor and process schema
    schema_processor = SchemaProcessor(db_url='sqlite:///example.db')
    schema_info = schema_processor.process_schema()
    
    # Optionally print schema info
    schema_processor.print_schema_info(schema_info)
    
    # Initialize Prompt Manager with schema keys
    prompt_manager = PromptManager(
        model_name='phi3:3.8b',
        temperature=0.7,
        max_tokens=512,
        schema=schema_processor.get_schema_keys()
    )
    
    # Example natural language input
    nl_input = "Show me all users who signed up in the last month."
    
    # Get response from the model
    response = prompt_manager.get_response(nl_input)
    
    # Print the response
    print("Model Response:")
    print(response)

if __name__ == "__main__":
    main()
