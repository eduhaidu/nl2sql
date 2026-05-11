from conversation_controller import ConversationController
import unit_tests
class TestConversationController(unit_tests.UnitTests):
    def test_conversation_controller(self):
        conversation_controller = ConversationController()
        self.assertIsNotNone(conversation_controller)

    def test_create_conversation(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        self.assertIsNotNone(conversation_id)

    def test_get_conversations(self):
        conversation_controller = ConversationController()
        conversations = conversation_controller.get_conversations("testuser")
        self.assertIsInstance(conversations, list)
    
    def test_get_conversation_history(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        history = conversation_controller.get_conversation_history(conversation_id)
        self.assertIsInstance(history, list)
    
    def test_add_message_to_conversation(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        result = conversation_controller.add_message_to_conversation(conversation_id, "user", "What is the total sales for last month?")
        self.assertTrue(result)

    def test_add_message_to_conversation_invalid_conversation(self):
        conversation_controller = ConversationController()
        result = conversation_controller.add_message_to_conversation(9999, "user", "What is the total sales for last month?")
        self.assertFalse(result)

    def test_add_message_to_conversation_empty_message(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        result = conversation_controller.add_message_to_conversation(conversation_id, "user", "")
        self.assertFalse(result)

    def test_add_message_to_conversation_long_message(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        long_message = "A" * 1001  # Assuming max length is 1000 characters
        result = conversation_controller.add_message_to_conversation(conversation_id, "user", long_message)
        self.assertFalse(result)

    def test_add_message_to_conversation_invalid_role(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        result = conversation_controller.add_message_to_conversation(conversation_id, "invalid_role", "What is the total sales for last month?")
        self.assertFalse(result)

    def test_add_message_to_conversation_sql_injection(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        sql_injection_message = "What is the total sales for last month?'; DROP TABLE conversations; --"
        result = conversation_controller.add_message_to_conversation(conversation_id, "user", sql_injection_message)
        self.assertFalse(result)

    def test_add_message_to_conversation_sql_injection_attempt(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        sql_injection_attempt_message = "What is the total sales for last month?'; SELECT * FROM conversations; --"
        result = conversation_controller.add_message_to_conversation(conversation_id, "user", sql_injection_attempt_message)
        self.assertFalse(result)

    def test_get_conversation_history_invalid_conversation(self):
        conversation_controller = ConversationController()
        history = conversation_controller.get_conversation_history(9999)
        self.assertIsNone(history)

    def test_get_conversation_history_no_messages(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        history = conversation_controller.get_conversation_history(conversation_id)
        self.assertEqual(history, [])

    def test_get_conversation_history_with_messages(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        conversation_controller.add_message_to_conversation(conversation_id, "user", "What is the total sales for last month?")
        history = conversation_controller.get_conversation_history(conversation_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][0], "What is the total sales for last month?")
        self.assertEqual(history[0][1], "user")

    def test_get_conversation_details(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        details = conversation_controller.get_conversation_details(conversation_id)
        self.assertIsNotNone(details)
        self.assertEqual(details["id"], conversation_id)

    def test_get_conversation_details_invalid_conversation(self):
        conversation_controller = ConversationController()
        details = conversation_controller.get_conversation_details(9999)
        self.assertIsNone(details)

    def test_get_conversation_details_empty_conversation(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        details = conversation_controller.get_conversation_details(conversation_id)
        self.assertIsNotNone(details)
        self.assertEqual(details["id"], conversation_id)

    def test_get_conversation_details_sql_injection(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        sql_injection_conversation_id = "9999; DROP TABLE conversations; --"
        details = conversation_controller.get_conversation_details(sql_injection_conversation_id)
        self.assertIsNone(details)

    def test_get_conversation_details_sql_injection_attempt(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        sql_injection_attempt_conversation_id = "9999; SELECT * FROM conversations; --"
        details = conversation_controller.get_conversation_details(sql_injection_attempt_conversation_id)
        self.assertIsNone(details)

    def test_get_conversations_no_conversations(self):
        conversation_controller = ConversationController()
        conversations = conversation_controller.get_conversations("user_with_no_conversations")
        self.assertEqual(conversations, [])

    def test_get_conversations_with_conversations(self):
        conversation_controller = ConversationController()
        conversation_controller.create_conversation("testuser")
        conversations = conversation_controller.get_conversations("testuser")
        self.assertGreaterEqual(len(conversations), 1)
    
    def test_get_conversations_sql_injection(self):
        conversation_controller = ConversationController()
        conversations = conversation_controller.get_conversations("testuser'; DROP TABLE conversations; --")
        self.assertIsNone(conversations)

    def test_get_conversations_sql_injection_attempt(self):
        conversation_controller = ConversationController()
        conversations = conversation_controller.get_conversations("testuser'; SELECT * FROM conversations; --")
        self.assertIsNone(conversations)

if __name__ == '__main__':    unit_tests.main()