from fastapi import FastAPI, Request
from pydantic import BaseModel
from agent import run_agent_with_memory, create_new_conversation
from utils.translator import detect_language, translate_to_english, translate_to_local
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from datetime import datetime

app = FastAPI()

# CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single global conversation memory
global_conversation = create_new_conversation()


class QueryInput(BaseModel):
    query: str


@app.post("/ask")
async def query_backend(q: QueryInput):
    if len(q.query or "") > 4000:
        return {"error": "Input is too long. Please limit to 4000 characters."}

    # Detect user language
    user_lang = detect_language(q.query)
    english_input = translate_to_english(q.query)

    print(f"[Lang: {user_lang}] Q: {english_input}")

    # Run agent with memory
    english_response, conversation_history = await run_agent_with_memory(
        english_input,
        global_conversation,
        user_lang
    )

    # Translate response back to user's language
    translated_response = translate_to_local(english_response, user_lang)

    # Return just the response as a simple string
    return {"response": translated_response}


@app.get("/conversation")
async def get_conversation_history():
    """Get conversation history"""
    return {
        "conversation_history": global_conversation.get("conversation_history", []),
        "created_at": global_conversation.get("created_at"),
        "last_activity": global_conversation.get("last_activity")
    }


@app.delete("/conversation")
async def clear_conversation():
    """Clear the conversation memory"""
    global global_conversation
    global_conversation = create_new_conversation()
    return {"message": "Conversation memory cleared successfully"}


@app.get("/")
async def healthcheck():
    return {"status": "up"}
