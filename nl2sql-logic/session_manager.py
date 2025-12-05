from typing import Dict
import uuid
from schema_processor import SchemaProcessor
from prompt_manager import PromptManager
from SQLAlchemySession import SQLAlchemySession

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, db_url: str) -> str:
        session_id = str(uuid.uuid4())

        schema_processor = SchemaProcessor(db_url)
        schema_info = schema_processor.process_schema()

        prompt_manager = PromptManager(schema=schema_info)

        sqlalchemy_session = SQLAlchemySession(db_url)

        self.sessions[session_id] = {
            "db_url": db_url,
            "schema_processor": schema_processor,
            "prompt_manager": prompt_manager,
            "sqlalchemy_session": sqlalchemy_session
        }
        return session_id
    
    def get_session(self, session_id: str) -> Dict:
        return self.sessions.get(session_id)
    
    def cleanup_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]