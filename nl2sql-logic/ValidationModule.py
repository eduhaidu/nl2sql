from prompt_manager import PromptManager
from schema_processor import SchemaProcessor
from SQLAlchemySession import SQLAlchemySession

class Validator:
    def __init__(self, sqlalchemy_session=None, prompt_manager=None, schema_processor=None):
        self.sqlalchemy_session = sqlalchemy_session or SQLAlchemySession()
        self.prompt_manager = prompt_manager or PromptManager()
        self.schema_processor = schema_processor or SchemaProcessor()

    def send_query_for_execution(self, query):
        try:
            result = self.sqlalchemy_session.execute(query)
            return result.fetchall()
        except Exception as e:
            return str(e)
        
    def calculate_execution_accuracy(self, execution_result, expected_result):
        if execution_result == expected_result:
            return 1.0
        return 0.0
        
    def validate_response(self, nl_input):
        schema_info = self.schema_processor.process_schema()
        filtered_schema = self.prompt_manager.filter_schema(schema_info)
        self.prompt_manager.schema = filtered_schema
        sql_query = self.prompt_manager.get_response(nl_input)
        execution_result = self.send_query_for_execution(sql_query)
        return {
            "sql_query": sql_query,
            "execution_result": execution_result
        }
    
    def generate_retry_prompt(self, nl_input, previous_sql, error_message=None):
        if(error_message):
            retry_prompt = (
                f"The previous SQL query generated was: {previous_sql}\n"
                f"However, it resulted in the following error when executed: {error_message}\n"
                f"Please generate a corrected SQL query for the following natural language input: {nl_input}"
            )
        else:
            retry_prompt = (
                f"The previous SQL query generated was: {previous_sql}\n"
                f"However, it did not return the expected results.\n"
                f"Please generate a corrected SQL query for the following natural language input: {nl_input}"
            )
        return retry_prompt
    
    def print_validation(self, nl_input):
        validation_result = self.validate_response(nl_input)
        print("Generated SQL Query:")
        print(validation_result["sql_query"])
        print("Execution Result:")
        print(validation_result["execution_result"])

