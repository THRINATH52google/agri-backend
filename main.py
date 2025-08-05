from fastapi import FastAPI, Request
from pydantic import BaseModel
from agent import run_agent_with_memory, create_new_conversation
from utils.translator import detect_language, translate_to_english, translate_to_local
from fastapi.middleware.cors import CORSMiddleware
from tools.disease_detector import detect_plant_disease
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, File, UploadFile, Form

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

class DiseaseInput(BaseModel):
    leaf_description: str

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


@app.post("/detect-disease")
async def detect_disease(file: UploadFile = File(...)):
    """Detect plant disease and suggest pesticides based on uploaded image"""

    try:
        # Validate image file
        if not file.content_type.startswith('image/'):
            return {"solution": "Please upload an image file (JPEG, PNG, etc.)"}

        if file.size > 10 * 1024 * 1024:  # 10MB limit
            return {"solution": "Image file too large. Please upload an image smaller than 10MB."}

        # Read image data
        image_data = await file.read()

        print(f"[Disease Detection] Image uploaded: {file.filename} ({len(image_data)} bytes)")

        # Detect disease and get recommendations (no description needed)
        english_result = detect_plant_disease("", image_data)

        # Return with 'solution' key to match frontend expectation
        return {"solution": english_result}

    except Exception as e:
        return {"solution": f"Error processing image: {str(e)}"}


@app.post("/detect-disease/")
async def detect_disease_with_slash(file: UploadFile = File(...)):
    """Same endpoint with trailing slash for compatibility"""
    return await detect_disease(file)