from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from NLInputModel import NLInputModel
from prompt_manager import PromptManager
from schema_processor import SchemaProcessor

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prompt_manager = PromptManager()
schema_processor = SchemaProcessor()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/nlinput")
def process_nl_input(data: NLInputModel):
    prompt_manager.nl_input = data.nl_input
    schema_info = schema_processor.process_schema()
    filtered_schema = prompt_manager.filter_schema(schema_info)
    prompt_manager.schema = filtered_schema
    response = prompt_manager.get_response(data.nl_input)
    return {"response": response}