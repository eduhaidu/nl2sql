from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class SQLAlchemySession:
    @staticmethod
    def get_session(db_url='sqlite:///example.db'):

        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        return Session()
    
    def __init__(self, db_url='sqlite:///example.db'):
        self.session = self.get_session(db_url)

    def execute_query(self, query):
        try:
            result = self.session.execute(query)
            return result.fetchall()
        except Exception as e:
            return str(e)