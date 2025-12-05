from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class SQLAlchemySession:
    @staticmethod
    def get_session(db_url):
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        return Session()
    
    def __init__(self, db_url='sqlite:///example.db'):
        self.session = self.get_session(db_url)

    def execute_query(self, query):
        try:
            result = self.session.execute(text(query.query))
            rows = result.fetchall()

            if rows:
                columns = result.keys()
                result_list = [dict(zip(columns, row)) for row in rows]
                return result_list
            else:
                return []
        except Exception as e:
            return str(e)