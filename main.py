from fastapi import FastAPI, Request
from pydantic import BaseModel
from agent import run_agent
from utils.translator import detect_language, translate_to_english, translate_to_local
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryInput(BaseModel):
    question: str

@app.post("/ask")
async def query_backend(q: QueryInput):
    if len(q.question or "") > 4000:
        return {"error": "Input is too long. Please limit to 4000 characters."}
    print("reached here")
    user_lang = detect_language(q.question)
    english_input = translate_to_english(q.question)

    print(f"[Original Lang: {user_lang}] Q: {english_input}")

    english_response = await run_agent(english_input,user_lang)
    translated_response = translate_to_local(english_response, user_lang)
    return translated_response

    # return {
    #     "original_input": q.question,
    #     "translated_question": english_input,
    #     "english_response": english_response,
    #     "translated_response": translated_response,
    #     "lang": user_lang
    # }
