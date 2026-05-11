from auth_controller import AuthController
import unit_tests
class TestAuthController(unit_tests.UnitTests):
    def test_auth_controller(self):
        auth_controller = AuthController()
        self.assertIsNotNone(auth_controller)

    def test_authenticate_user(self):
        auth_controller = AuthController()
        result = auth_controller.authenticate_user("testuser", "testpassword")
        self.assertTrue(result)

    def test_authenticate_user_invalid(self):
        auth_controller = AuthController()
        result = auth_controller.authenticate_user("invaliduser", "invalidpassword")
        self.assertFalse(result)

    def test_authenticate_user_empty(self):
        auth_controller = AuthController()
        result = auth_controller.authenticate_user("", "")
        self.assertFalse(result)

    def test_authenticate_user_sql_injection(self):
        auth_controller = AuthController()
        result = auth_controller.authenticate_user("testuser' OR '1'='1", "testpassword' OR '1'='1")
        self.assertFalse(result)

    def test_authenticate_user_sql_injection_attempt(self):
        auth_controller = AuthController()
        result = auth_controller.authenticate_user("testuser'; DROP TABLE users; --", "testpassword")
        self.assertFalse(result)

    def test_authenticate_user_sql_injection_attempt_2(self):
        auth_controller = AuthController()
        result = auth_controller.authenticate_user("testuser'; SELECT * FROM users; --", "testpassword")
        self.assertFalse(result)

    def test_register_user(self):
        auth_controller = AuthController()
        result = auth_controller.register_user("newuser", "newpassword")
        self.assertTrue(result)

    def test_register_user_existing(self):
        auth_controller = AuthController()
        result = auth_controller.register_user("testuser", "testpassword")
        self.assertFalse(result)

    def test_register_user_empty(self):
        auth_controller = AuthController()
        result = auth_controller.register_user("", "")
        self.assertFalse(result)

    def test_register_user_sql_injection(self):
        auth_controller = AuthController()
        result = auth_controller.register_user("newuser'; DROP TABLE users; --", "newpassword")
        self.assertFalse(result)

    def test_register_user_sql_injection_attempt(self):
        auth_controller = AuthController()
        result = auth_controller.register_user("newuser'; SELECT * FROM users; --", "newpassword")
        self.assertFalse(result)

    def test_get_user_id(self):
        auth_controller = AuthController()
        user_id = auth_controller.get_user_id("testuser")
        self.assertIsNotNone(user_id)

    def test_get_user_id_empty(self):
        auth_controller = AuthController()
        user_id = auth_controller.get_user_id("")
        self.assertIsNone(user_id)

    def test_get_user_id_sql_injection(self):
        auth_controller = AuthController()
        user_id = auth_controller.get_user_id("testuser'; DROP TABLE users; --")
        self.assertIsNone(user_id)

    def test_get_user_id_sql_injection_attempt(self):
        auth_controller = AuthController()
        user_id = auth_controller.get_user_id("testuser'; SELECT * FROM users; --")
        self.assertIsNone(user_id)

    def test_check_sql_injection(self):
        auth_controller = AuthController()
        self.assertTrue(auth_controller.check_sql_injection("testuser'; DROP TABLE users; --"))
        self.assertTrue(auth_controller.check_sql_injection("testuser'; SELECT * FROM users; --"))
        self.assertFalse(auth_controller.check_sql_injection("normalusername"))
        
if __name__ == '__main__':    unit_tests.main()