from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
from agent import run_agent_with_memory, create_new_conversation
from utils.translator import detect_language, translate_to_english, translate_to_local
from utils.voice_utils_simple import voice_processor, logger
from fastapi.middleware.cors import CORSMiddleware
from typing import  Optional
from tools.disease_detector import detect_plant_disease
import base64
import logging
import speech_recognition as sr
import tempfile
import os

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


class VoiceQueryInput(BaseModel):
    audio_data: str  # Base64 encoded audio
    language: Optional[str] = "auto"
    session_id: Optional[str] = None


class DiseaseInput(BaseModel):
    leaf_description: str


@app.post("/ask")
async def query_backend(q: QueryInput):
    if len(q.query or "") > 4000:
        return {"response": "Input is too long. Please limit to 4000 characters."}

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


@app.post("/detect-disease-text-only")
async def detect_disease_text_only(d: DiseaseInput):
    """Detect plant disease based on text description only (for backward compatibility)"""
    try:
        if len(d.leaf_description or "") > 2000:
            return {"response": "Description is too long. Please limit to 2000 characters."}

        # Detect user language
        user_lang = detect_language(d.leaf_description)
        english_description = translate_to_english(d.leaf_description)

        print(f"[Disease Detection] [Lang: {user_lang}] Description: {english_description}")

        # Detect disease and get recommendations
        english_result = detect_plant_disease(english_description)

        # Translate result back to user's language
        translated_result = translate_to_local(english_result, user_lang)

        return {"response": translated_result}

    except Exception as e:
        return {"response": f"Error processing your request: {str(e)}"}


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


@app.post("/voice/ask")
async def voice_query_backend(vq: VoiceQueryInput):
    print("/ask")
    try:
        import base64

        # Decode base64 audio data
        audio_bytes = base64.b64decode(vq.audio_data)

        logger.info(f"Received audio data: {len(audio_bytes)} bytes")

        # Validate audio format with better error handling
        if not voice_processor.validate_audio_format(audio_bytes):
            supported_formats = voice_processor.get_supported_audio_formats()
            logger.error(f"Invalid audio format. Data length: {len(audio_bytes)} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio format. Supported formats: {', '.join(supported_formats)}. Received {len(audio_bytes)} bytes."
            )

        logger.info("Audio format validation passed")

        # Try online recognition with Indian language priority
        transcribed_text, detected_language = voice_processor.speech_to_text(
            audio_bytes,
            vq.language
        )

        # If online recognition fails, try offline
        if not transcribed_text:
            logger.info("Online recognition failed, trying offline recognition...")
            transcribed_text, detected_language = voice_processor.speech_to_text_offline(audio_bytes)

        logger.info(f"Speech recognition result: '{transcribed_text}' (lang: {detected_language})")

        if not transcribed_text:
            return {
                "error": "Could not understand speech. Please try again.",
                "transcribed_text": "",
                "detected_language": detected_language,
                "response": "",
                "audio_response": ""
            }

        # Process the transcribed text through existing agent
        english_input = translate_to_english(transcribed_text)

        print(f"[Voice] [Lang: {detected_language}] Transcribed: {transcribed_text}")
        print(f"[Voice] English: {english_input}")

        # Run agent with memory
        english_response, conversation_history = await run_agent_with_memory(
            english_input,
            global_conversation,
            detected_language
        )

        # Translate response back to user's language
        translated_response = translate_to_local(english_response, detected_language)

        # Convert response to speech in the detected language
        audio_response = voice_processor.text_to_speech(translated_response, detected_language)
        audio_response_b64 = base64.b64encode(audio_response).decode('utf-8')

        return {
            "transcribed_text": transcribed_text,
            "detected_language": detected_language,
            "response": translated_response,
            "audio_response": audio_response_b64,
            "session_id": vq.session_id,
            "conversation_history": conversation_history
        }

    except Exception as e:
        logger.error(f"Voice processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice processing error: {str(e)}")


@app.post("/voice/ask-file")
async def voice_query_file(
        audio_file: UploadFile = File(...),
        language: str = Form("auto"),
        session_id: Optional[str] = Form(None)
):
    """
    Voice query endpoint that accepts audio file upload
    """
    print("/ask-file")
    try:
        # Validate file type more broadly
        if not audio_file.content_type.startswith(('audio/', 'video/')):
            supported_formats = voice_processor.get_supported_audio_formats()
            raise HTTPException(
                status_code=400,
                detail=f"Please upload an audio file. Supported formats: {', '.join(supported_formats)}"
            )

        if audio_file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Audio file too large. Please upload a file smaller than 10MB.")

        # Read audio data
        audio_data = await audio_file.read()

        # Convert to base64 for processing
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')

        # Use the existing voice endpoint
        voice_input = VoiceQueryInput(
            audio_data=audio_b64,
            language=language,
            session_id=session_id
        )

        return await voice_query_backend(voice_input)

    except Exception as e:
        logging.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")


@app.get("/voice/supported-languages")
async def get_supported_languages():
    """
    Get list of supported languages for voice processing
    """
    return voice_processor.get_supported_languages()


@app.post("/voice/text-to-speech")
async def text_to_speech_endpoint(text: str, language: str = "en"):
    """
    Convert text to speech
    """
    try:
        audio_bytes = voice_processor.text_to_speech(text, language)
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        return {
            "audio_data": audio_b64,
            "language": language,
            "text": text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech error: {str(e)}")


@app.post("/voice/speech-to-text")
async def speech_to_text_endpoint(
        audio_file: UploadFile = File(...),
        language: str = Form("auto")
):
    """
    Convert speech to text
    """
    try:
        # Validate file type
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Please upload an audio file")

        # Read audio data
        audio_data = await audio_file.read()

        # Convert to WAV if needed
        audio_data = voice_processor.convert_audio_format(audio_data, "wav")

        # Speech to text
        transcribed_text, detected_language = voice_processor.speech_to_text(
            audio_data,
            language
        )

        return {
            "transcribed_text": transcribed_text,
            "detected_language": detected_language,
            "original_language": language
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech-to-text error: {str(e)}")


@app.post("/voice/test-audio")
async def test_audio_endpoint(vq: VoiceQueryInput):
    """
    Test endpoint to debug audio processing
    """
    try:
        import base64

        # Decode base64 audio data
        audio_bytes = base64.b64decode(vq.audio_data)

        logger.info(f"Test: Received audio data: {len(audio_bytes)} bytes")

        # Validate audio format
        if not voice_processor.validate_audio_format(audio_bytes):
            return {"error": "Invalid audio format"}

        # Convert to audio segment
        audio_segment = voice_processor._convert_audio_to_segment(audio_bytes)
        
        # Save debug file
        debug_file = "test_audio.wav"
        audio_segment.export(debug_file, format='wav')
        
        # Analyze audio properties
        audio_info = {
            "duration_seconds": audio_segment.duration_seconds,
            "channels": audio_segment.channels,
            "frame_rate": audio_segment.frame_rate,
            "dBFS": audio_segment.dBFS,
            "sample_width": audio_segment.sample_width,
            "max_possible_amplitude": audio_segment.max_possible_amplitude,
            "rms": audio_segment.rms
        }
        
        # Check if audio has any significant content
        has_content = audio_segment.dBFS > -50 and audio_segment.duration_seconds > 0.5
        
        return {
            "audio_info": audio_info,
            "debug_file": debug_file,
            "has_content": has_content,
            "message": "Audio saved for inspection"
        }

    except Exception as e:
        logger.error(f"Test audio error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test audio error: {str(e)}")
