from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from NLInputModel import NLInputModel
from DBURLInputModel import DBURLInputModel
from session_manager import SessionManager

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
    return {"response": response}

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