from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from NLInputModel import NLInputModel
from DBURLInputModel import DBURLInputModel
from QueryModel import QueryModel
from session_manager import SessionManager
from QueryExtractor import extract_sql_query
from ValidationModule import Validator
app = FastAPI()

# CORS configuration - allow both localhost and 127.0.0.1
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

session_manager = SessionManager()

@app.get("/")
def read_root():
    return {"Hello": "World", "active_sessions": len(session_manager.sessions)}

@app.delete("/disconnect/{session_id}")
def disconnect_session(session_id: str):
    """Cleanup session when user disconnects or switches databases"""
    session_manager.cleanup_session(session_id)
    return {"message": "Session disconnected successfully"}

@app.post("/nlinput")
def process_nl_input(data: NLInputModel):
    session_id = data.session_id
    if not session_id:
        return {"error": "Session ID is required."}
    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Invalid session ID."}
    prompt_manager = session["prompt_manager"]
    response = prompt_manager.get_response(data.nl_input)
    query = extract_sql_query(response)
    return {"response": response, "query": query}

@app.post("/dbupdate")
def update_database_url(data: DBURLInputModel):
    if not data.database_url:
        return {"error": "Database URL is required."}
    
    try:
        # Create a new session
        session_id = session_manager.create_session(data.database_url)
        return {"message": "Database URL updated and session created.", "session_id": session_id}
    except ValueError as e:
        return {"error": str(e)}
    
@app.post("/executesql/{session_id}")
def execute_sql_query(session_id: str, query: QueryModel):
    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Invalid session ID."}
    
    try:
        sqlalchemy_session = session["sqlalchemy_session"]
        result = sqlalchemy_session.execute_query(query)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/validate/{session_id}")
def validate_nl_input(session_id: str, data: NLInputModel):
    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Invalid session ID."}
    
    try:
        sqlalchemy_session = session["sqlalchemy_session"]
        prompt_manager = session["prompt_manager"]
        schema_processor = session["schema_processor"]
        
        validator = Validator(
            sqlalchemy_session=sqlalchemy_session,
            prompt_manager=prompt_manager,
            schema_processor=schema_processor
        )
        
        validation_result = validator.validate_response(data.nl_input)
        return validation_result
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/retry/{session_id}")
def generate_retry_prompt(session_id: str, data: NLInputModel, previous_sql: str, error_message: str = None):
    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Invalid session ID."}
    
    try:
        prompt_manager = session["prompt_manager"]
        sqlalchemy_session = session["sqlalchemy_session"]
        schema_processor = session["schema_processor"]
        
        validator = Validator(
            sqlalchemy_session=sqlalchemy_session,
            prompt_manager=prompt_manager,
            schema_processor=schema_processor
        )
        
        retry_prompt = validator.generate_retry_prompt(
            nl_input=data.nl_input,
            previous_sql=previous_sql,
            error_message=error_message
        )
        return {"retry_prompt": retry_prompt}
    except Exception as e:
        return {"error": str(e)}