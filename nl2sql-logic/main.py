from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from NLInputModel import NLInputModel
from DBURLInputModel import DBURLInputModel
from QueryModel import QueryModel
from FeedbackModel import FeedbackModel
from ConversationNameModel import ConversationNameModel
from session_manager import SessionManager
from QueryExtractor import extract_sql_query
from ValidationModule import Validator
from conversation_controller import (
    create_conversation, 
    get_conversations, 
    get_conversation_history, 
    add_message_to_conversation, 
    get_conversation_details, 
    rename_conversation as rename_conversation_db,  # ← Alias to avoid name collision
    delete_conversation
)
from result_storage import ResultStorage
from feedback_storage import FeedbackStorage
from example_manager import ExampleManager
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

def check_if_query_uses_schema(query, schema_info):
    # Simple heuristic: check if any table or column names from the schema are present in the query
    for table in schema_info.get("tables", []):
        if table["name"].lower() in query.lower():
            return True
        for column in table.get("columns", []):
            if column["name"].lower() in query.lower():
                return True
    return False

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

@app.put("/conversations/{conversation_id}")
def rename_conversation(conversation_id: str, new_name: ConversationNameModel):
    success = rename_conversation_db(conversation_id, new_name.name)  # ← Now calls the controller function
    if success:
        return {"message": f"Conversation renamed to {new_name.name} successfully."}
    else:       
        return {"error": "Failed to rename conversation."}

@app.delete("/conversations/{conversation_id}")
def delete_conversation_endpoint(conversation_id: str):
    delete_conversation(conversation_id)
    # Also cleanup any associated session
    for sid, session in list(session_manager.sessions.items()):
        if session.get("conversation_id") == conversation_id:
            session_manager.cleanup_session(sid)
            print(f"Deleted session {sid} associated with conversation {conversation_id}")
    return {"message": "Conversation and associated sessions deleted successfully."}

@app.post("/executesql/{session_id}")
def execute_sql_query(session_id: str, query: QueryModel):
    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Invalid session ID."}
    if "SELECT" not in query.query.upper():
        return {"error": "Only SELECT queries are allowed for execution."}
    # schema_processor = session["schema_processor"]
    # schema_info = schema_processor.process_schema()
    # if not check_if_query_uses_schema(query.query, schema_info):
    #     return {"error": "The query does not appear to use the database schema. Please ensure your query references the correct tables and columns."}
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
        schema_info = schema_processor.process_schema()
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
        
        retry_data = validator.generate_retry_prompt(
            nl_input=data.nl_input,
            previous_sql=previous_sql,
            error_message=error_message
        )

        prompt_manager.nl_input = retry_data["original_question"]  # Set the original question as the NL input for context
        
        full_prompt = prompt_manager.get_response(retry_data["original_question"])
        full_prompt = retry_data["original_question"] + "\n\n" + full_prompt
        
        prompt_manager.conversation_history.append({"role": "user", "content": full_prompt})

        response = prompt_manager.client.chat(
            model=prompt_manager.model_name,
            message=prompt_manager.conversation_history
        )

        prompt_manager.conversation_history.append({"role": "assistant", "content": response.message["content"]})
        new_sql_query = extract_sql_query(response.message["content"])
        return {"response": response, "query": new_sql_query}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/feedback/{conversation_id}")
def submit_feedback(conversation_id: str, feedback: FeedbackModel):
    """Store feedback and update production examples pool"""
    feedback_storage = FeedbackStorage()
    feedback_storage.store_feedback(conversation_id, feedback)
    
    example_manager = ExampleManager()

    # Add successful queries to production examples pool
    if feedback.feedback_type in ["positive", "correct"]:
        example_manager.add_production_example(feedback.user_question, feedback.generated_sql)
        print(f"Added successful query to production examples: {feedback.user_question}")

    # Add corrected queries to production examples pool
    if feedback.feedback_type in ["negative", "incorrect"] and feedback.corrected_sql:
        example_manager.add_corrected_example(
            feedback.user_question, 
            feedback.generated_sql, 
            feedback.corrected_sql
        )
        print(f"Added corrected query to production examples: {feedback.user_question}")

    return {"message": "Feedback submitted successfully."}