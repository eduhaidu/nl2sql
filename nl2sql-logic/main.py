from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from NLInputModel import NLInputModel
from DBURLInputModel import DBURLInputModel
from QueryModel import QueryModel
from session_manager import SessionManager
from QueryExtractor import extract_sql_query
from ValidationModule import Validator
from conversation_controller import create_conversation, get_conversations, get_conversation_history, add_message_to_conversation, get_conversation_details
from result_storage import ResultStorage
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
    add_message_to_conversation(session["conversation_id"], data.nl_input, "user")
    add_message_to_conversation(session["conversation_id"], response, "assistant")
    return {"response": response, "query": query}

@app.post("/dbimport")
def update_database_url(data: DBURLInputModel):
    if not data.database_url:
        return {"error": "Database URL is required."}
    
    try:
        # Create a new conversation for this database connection
        conversation_id = create_conversation(data.database_url, data.database_type)
        print(f"New conversation created with ID: {conversation_id}")
        # Create a new session
        session_id = session_manager.create_session(data.database_url, database_type=data.database_type, conversation_id=conversation_id)
        return {"message": "Database URL updated and session created.", "session_id": session_id, "conversation_id": conversation_id}
    except ValueError as e:
        return {"error": str(e)}
    
@app.get("/conversations")
def list_conversations():
    conversations = get_conversations()
    if conversations is None:
        return {"error": "Failed to retrieve conversations."}
    return {"conversations": conversations}

@app.get("/conversations/{conversation_id}")
def conversation_history(conversation_id: str):
    history = get_conversation_history(conversation_id)
    if history is None:
        return {"error": "Failed to retrieve conversation history."}
    
    # Get conversation details (including db_url)
    conversation = get_conversation_details(conversation_id)
    if not conversation:
        return {"error": "Conversation not found."}
    
    # Find or create the session_id for this conversation_id
    session_id = None
    for sid, session in session_manager.sessions.items():
        if session.get("conversation_id") == conversation_id:
            session_id = sid
            break
    
    # If no session exists, recreate it from the stored db_url
    if not session_id:
        print(f"No session found for conversation {conversation_id}, recreating...")
        session_id = session_manager.create_session(
            conversation["db_url"],
            database_type=conversation.get("database_type"),
            conversation_id=conversation_id
        )
        print(f"Session recreated with ID: {session_id}")
    
    # Always sync conversation history from PostgreSQL to PromptManager
    session = session_manager.get_session(session_id)
    if session and history:
        session["prompt_manager"].load_conversation_history(history)
        print(f"Synced {len(history)} messages to PromptManager for conversation {conversation_id}")
    
    # Format history as messages with user_message and assistant_response
    messages = []
    for i in range(0, len(history), 2):
        msg_dict = {}
        if i < len(history) and history[i][1] == "user":
            msg_dict["user_message"] = history[i][0]
        if i + 1 < len(history) and history[i + 1][1] == "assistant":
            msg_dict["assistant_response"] = history[i + 1][0]
        if msg_dict:
            messages.append(msg_dict)
    
    return {
        "conversation_id": conversation_id,
        "session_id": session_id,
        "messages": messages
    }

@app.post("/executesql/{session_id}")
def execute_sql_query(session_id: str, query: QueryModel):
    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Invalid session ID."}
    
    try:
        sqlalchemy_session = session["sqlalchemy_session"]
        result = sqlalchemy_session.execute_query(query)
        # Store the result in the database
        result_storage = ResultStorage()
        result_storage.save_query_execution(session["conversation_id"], query.query, result)
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
        
        response = prompt_manager.get_response(retry_prompt)
        new_sql_query = extract_sql_query(response)
        add_message_to_conversation(session["conversation_id"], retry_prompt, "user")
        add_message_to_conversation(session["conversation_id"], response, "assistant")
        return {"response": response, "query": new_sql_query}
    except Exception as e:
        return {"error": str(e)}