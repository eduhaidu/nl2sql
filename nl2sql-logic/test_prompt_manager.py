import unit_tests
from prompt_manager import PromptManager
class TestPromptManager(unit_tests.UnitTests):
    def test_prompt_manager(self):
        
        prompt_manager = PromptManager()
        self.assertIsNotNone(prompt_manager)

    def test_initialize_context(self):
        prompt_manager = PromptManager()
        context = prompt_manager._initialize_context()
        self.assertIsNotNone(context)

    def test_initialize_sentence_transformer(self):
        prompt_manager = PromptManager()
        sentence_transformer = prompt_manager.initialize_sentence_transformer()
        self.assertIsNotNone(sentence_transformer)

    def test_filter_relevant_tables(self):
        prompt_manager = PromptManager()
        context = prompt_manager._initialize_context()
        relevant_tables = prompt_manager.filter_relevant_tables("What is the total sales for last month?")
        self.assertIsNotNone(relevant_tables)

    def test_get_response(self):
        prompt_manager = PromptManager()
        response = prompt_manager.get_response("What is the total sales for last month?")
        self.assertIsNotNone(response)

if __name__ == '__main__':    unit_tests.main()