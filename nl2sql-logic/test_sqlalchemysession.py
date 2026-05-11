from SQLAlchemySession import SQLAlchemySession
import unit_tests
class TestSQLAlchemySession(unit_tests.UnitTests):
    def test_sqlalchemy_session(self):
        session = SQLAlchemySession()
        self.assertIsNotNone(session)

    def test_execute_query(self):
        session = SQLAlchemySession()
        result = session.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
        self.assertIsInstance(result, list)

if __name__ == '__main__':
    unit_tests.main()