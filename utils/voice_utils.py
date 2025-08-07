# import speech_recognition as sr
# from gtts import gTTS
# import io
# import base64
# import tempfile
# import os
# from pydub import AudioSegment
# from pydub.playback import play
# import numpy as np
# from typing import Tuple, Optional
# import logging
#
# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# class VoiceProcessor:
#     def __init__(self):
#         self.recognizer = sr.Recognizer()
#         self.recognizer.energy_threshold = 4000
#         self.recognizer.dynamic_energy_threshold = True
#         self.recognizer.pause_threshold = 0.8
#
#     def speech_to_text(self, audio_data: bytes, language: str = "auto") -> Tuple[str, str]:
#         """
#         Convert speech to text with language detection
#
#         Args:
#             audio_data: Raw audio bytes
#             language: Language code for recognition (e.g., 'te-IN', 'hi-IN', 'en-IN')
#
#         Returns:
#             Tuple of (transcribed_text, detected_language)
#         """
#         try:
#             # Convert bytes to AudioData
#             audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
#
#             # Try with specified language first
#             if language != "auto":
#                 try:
#                     text = self.recognizer.recognize_google(
#                         audio,
#                         language=language,
#                         show_all=False
#                     )
#                     return text, language
#                 except sr.UnknownValueError:
#                     logger.warning(f"Could not recognize speech with language {language}")
#
#             # Try with auto-detection
#             try:
#                 text = self.recognizer.recognize_google(
#                     audio,
#                     language="auto",
#                     show_all=False
#                 )
#                 # For auto-detection, we'll need to detect language from text
#                 from .translator import detect_language
#                 detected_lang = detect_language(text)
#                 return text, detected_lang
#             except sr.UnknownValueError:
#                 return "", "en"
#             except sr.RequestError as e:
#                 logger.error(f"Speech recognition service error: {e}")
#                 return "", "en"
#
#         except Exception as e:
#             logger.error(f"Speech to text error: {e}")
#             return "", "en"
#
#     def text_to_speech(self, text: str, language: str = "en") -> bytes:
#         """
#         Convert text to speech
#
#         Args:
#             text: Text to convert to speech
#             language: Language code (e.g., 'te', 'hi', 'en')
#
#         Returns:
#             Audio bytes in MP3 format
#         """
#         try:
#             # Map language codes to gTTS language codes
#             lang_mapping = {
#                 'te': 'te',  # Telugu
#                 'hi': 'hi',  # Hindi
#                 'en': 'en',  # English
#                 'es': 'es',  # Spanish
#                 'fr': 'fr',  # French
#                 'de': 'de',  # German
#             }
#
#             tts_lang = lang_mapping.get(language, 'en')
#
#             # Create gTTS object
#             tts = gTTS(text=text, lang=tts_lang, slow=False)
#
#             # Save to temporary file
#             with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
#                 tts.save(temp_file.name)
#
#                 # Read the file and convert to bytes
#                 with open(temp_file.name, 'rb') as f:
#                     audio_bytes = f.read()
#
#                 # Clean up temporary file
#                 os.unlink(temp_file.name)
#
#                 return audio_bytes
#
#         except Exception as e:
#             logger.error(f"Text to speech error: {e}")
#             # Return empty bytes on error
#             return b""
#
#     def get_supported_languages(self) -> dict:
#         """
#         Get list of supported languages for voice processing
#         """
#         return {
#             "telugu": {
#                 "code": "te",
#                 "speech_recognition": "te-IN",
#                 "text_to_speech": "te",
#                 "display_name": "తెలుగు"
#             },
#             "hindi": {
#                 "code": "hi",
#                 "speech_recognition": "hi-IN",
#                 "text_to_speech": "hi",
#                 "display_name": "हिंदी"
#             },
#             "english": {
#                 "code": "en",
#                 "speech_recognition": "en-IN",
#                 "text_to_speech": "en",
#                 "display_name": "English"
#             },
#             "marathi": {
#                 "code": "mr",
#                 "speech_recognition": "mr-IN",
#                 "text_to_speech": "mr",
#                 "display_name": "मराठी"
#             },
#             "gujarati": {
#                 "code": "gu",
#                 "speech_recognition": "gu-IN",
#                 "text_to_speech": "gu",
#                 "display_name": "ગુજરાતી"
#             },
#             "bengali": {
#                 "code": "bn",
#                 "speech_recognition": "bn-IN",
#                 "text_to_speech": "bn",
#                 "display_name": "বাংলা"
#             }
#         }
#
#     def validate_audio_format(self, audio_data: bytes) -> bool:
#         """
#         Validate if audio data is in supported format
#         """
#         try:
#             # Try to load audio with pydub
#             audio = AudioSegment.from_file(io.BytesIO(audio_data))
#             return True
#         except Exception:
#             return False
#
#     def convert_audio_format(self, audio_data: bytes, target_format: str = "wav") -> bytes:
#         """
#         Convert audio to target format
#         """
#         try:
#             audio = AudioSegment.from_file(io.BytesIO(audio_data))
#
#             # Export to target format
#             output = io.BytesIO()
#             audio.export(output, format=target_format)
#             return output.getvalue()
#
#         except Exception as e:
#             logger.error(f"Audio conversion error: {e}")
#             return audio_data
#
#
# # Global voice processor instance
# voice_processor = VoiceProcessor()