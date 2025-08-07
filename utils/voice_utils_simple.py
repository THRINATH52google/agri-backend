# utils/voice_utils_simple.py
import speech_recognition as sr
from gtts import gTTS
import io
import base64
import tempfile
import os
from pydub import AudioSegment
import numpy as np
from typing import Tuple, Optional, List
import logging
import subprocess
import whisper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if ffmpeg is available
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Only set ffmpeg paths if ffmpeg is available
if check_ffmpeg():
    logger.info("FFmpeg found in PATH")
else:
    # Try to find ffmpeg in common locations
    possible_paths = [
        "C:\\ffmpeg\\bin\\",
        "C:\\Program Files\\ffmpeg\\bin\\",
        "C:\\Users\\ujvsp\\Downloads\\ffmpeg-7.1.1-essentials_build\\ffmpeg-7.1.1-essentials_build\\bin\\",
        os.path.join(os.path.dirname(__file__), "..", "..", "ffmpeg", "bin")
    ]
    
    ffmpeg_found = False
    for path in possible_paths:
        if os.path.exists(os.path.join(path, "ffmpeg.exe")):
            AudioSegment.converter = os.path.join(path, "ffmpeg.exe")
            AudioSegment.ffprobe = os.path.join(path, "ffprobe.exe")
            logger.info(f"Using ffmpeg from: {path}")
            ffmpeg_found = True
            break
    
    if not ffmpeg_found:
        logger.warning("FFmpeg not found. Audio processing may not work properly.")
        # Set dummy paths to avoid errors
        AudioSegment.converter = "ffmpeg"
        AudioSegment.ffprobe = "ffprobe"

class SimpleVoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Use the original settings that were working
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.1  # Lower phrase threshold
        self.recognizer.non_speaking_duration = 0.3  # Shorter non-speaking duration

    ####################################################
    # New helper: detect format from the first bytes
    ####################################################
    def detect_format_from_bytes(self, b: bytes) -> Optional[str]:
        # Look at file signatures (magic numbers)
        if len(b) < 12:
            return None
        header = b[:12]

        # WAV: "RIFF" and "WAVE" in header
        if header[0:4] == b'RIFF' and header[8:12] == b'WAVE':
            return 'wav'
        # MP3: frame sync 0xFF FB or 'ID3'
        if header[0:3] == b'ID3' or header[0] == 0xFF:
            # Could be mp3 - hope for the best
            return 'mp3'
        # OGG: 'OggS'
        if header[0:4] == b'OggS':
            return 'ogg'
        # WEBM/Matroska: EBML header (0x1A 45 DF A3) for mkv/webm
        if header[0:4] == b'\x1A\x45\xDF\xA3':
            # webm uses Matroska; treat as webm
            return 'webm'
        # MP4/M4A: ftyp box after 4 bytes (e.g., 'ftyp')
        if b[4:8] == b'ftyp':
            # Could be mp4/m4a
            return 'mp4'
        # FLAC: "fLaC"
        if header[0:4] == b'fLaC':
            return 'flac'
        # AMR: "#!AMR\n"
        if header[:5] == b'#!AMR':
            return 'amr'
        # 3GP: similar to mp4/ftyp
        # fallback: None
        return None

    ####################################################
    # Conversion + validation helpers (use format hint if possible)
    ####################################################
    def _convert_audio_to_segment(self, audio_data: bytes) -> AudioSegment:
        """
        Convert raw audio bytes to AudioSegment, handling various formats.
        Uses header-based detection and passes explicit format to pydub to avoid ffprobe.
        """
        # First try to detect format from bytes
        fmt = self.detect_format_from_bytes(audio_data)
        logger.info(f"Detected format from bytes: {fmt}")

        # Try using the format hint
        try:
            if fmt:
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format=fmt)
            else:
                # If no hint, try without format (this triggers ffprobe)
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            return audio_segment
        except Exception as e:
            logger.warning(f"Error converting audio to segment using format={fmt}: {e}")

        # Fallback: write to a temp file with guessed suffix and try again
        try:
            suffix = f".{fmt}" if fmt else ".tmp"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                temp_name = temp_file.name

            # Try loading from file with format hint if available
            try:
                if fmt:
                    audio_segment = AudioSegment.from_file(temp_name, format=fmt)
                else:
                    audio_segment = AudioSegment.from_file(temp_name)
                return audio_segment
            finally:
                try:
                    os.unlink(temp_name)
                except Exception:
                    pass
        except Exception as e2:
            logger.error(f"Alternative audio conversion failed: {e2}")
            raise ValueError(f"Unsupported audio format: {e2}")

    def validate_audio_format(self, audio_data: bytes) -> bool:
        """
        Validate if audio data is in supported format with better error handling
        """
        try:
            fmt = self.detect_format_from_bytes(audio_data)
            logger.info(f"validate_audio_format, detected: {fmt}")
            
            if fmt:
                # If we detected the format, try loading with explicit format
                try:
                    AudioSegment.from_file(io.BytesIO(audio_data), format=fmt)
                    return True
                except Exception as e:
                    logger.warning(f"Failed to load with detected format {fmt}: {e}")
            
            # Try without format specification
            try:
                AudioSegment.from_file(io.BytesIO(audio_data))
                return True
            except Exception as e:
                logger.warning(f"Failed to load without format specification: {e}")
            
            # Fallback: write temp file and try
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
                    temp_file.write(audio_data)
                    temp_file.flush()
                    temp_name = temp_file.name
                
                try:
                    AudioSegment.from_file(temp_name)
                    return True
                finally:
                    try:
                        os.unlink(temp_name)
                    except Exception:
                        pass
            except Exception as e2:
                logger.warning(f"Alternative audio validation failed: {e2}")
                return False
                
        except Exception as e:
            logger.error(f"Audio validation error: {e}")
            return False

    def convert_audio_format(self, audio_data: bytes, target_format: str = "wav") -> bytes:
        """
        Convert audio to target format
        """
        try:
            # Use detected format if possible
            audio_segment = self._convert_audio_to_segment(audio_data)

            # Export to target format into BytesIO
            output = io.BytesIO()
            audio_segment.export(output, format=target_format)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            # If conversion fails, return original bytes (caller must handle)
            return audio_data

    ####################################################
    # Speech to text & TTS (unchanged, but use new helpers)
    ####################################################
    def _process_audio_for_indian_languages(self, audio_segment):
        """
        Apply specific processing for Indian languages using correct pydub methods
        """
        # Indian languages often have different frequency characteristics
        # Telugu and Hindi have more emphasis on certain frequency ranges
        
        # Apply high-pass and low-pass filters to focus on speech frequencies
        audio_segment = audio_segment.high_pass_filter(300)
        audio_segment = audio_segment.low_pass_filter(3400)
        
        # Apply more aggressive normalization
        if audio_segment.dBFS < -20:
            audio_segment = audio_segment + 15
        
        # Apply compression to even out volume (if available)
        try:
            audio_segment = audio_segment.compress_dynamic_range()
        except:
            # If compress_dynamic_range is not available, just normalize
            pass
        
        return audio_segment

    def speech_to_text(self, audio_data: bytes, language: str = "auto") -> Tuple[str, str]:
        try:
            logger.info(f"Starting speech_to_text with {len(audio_data)} bytes, language: {language}")
            
            audio_segment = self._convert_audio_to_segment(audio_data)
            logger.info(f"Audio segment created: {audio_segment.duration_seconds:.2f}s, {audio_segment.channels} channels, {audio_segment.frame_rate}Hz")

            # Save debug audio file to inspect
            debug_file = "debug_audio.wav"
            audio_segment.export(debug_file, format='wav')
            logger.info(f"Saved debug audio to: {debug_file}")

            # Simple processing that was working before
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
            
            # Basic normalization
            current_dbfs = audio_segment.dBFS
            logger.info(f"Original audio dBFS: {current_dbfs}")
            
            if current_dbfs < -30:
                audio_segment = audio_segment + 20
            
            logger.info(f"Processed audio dBFS: {audio_segment.dBFS}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
                audio_segment.export(temp_wav.name, format='wav', parameters=["-acodec", "pcm_s16le"])
                temp_name = temp_wav.name
                logger.info(f"Exported processed WAV file: {temp_name}")

            with open(temp_name, 'rb') as wav_file:
                wav_data = wav_file.read()
                logger.info(f"WAV data size: {len(wav_data)} bytes")
            try:
                os.unlink(temp_name)
            except Exception:
                pass

            # Do NOT skip the header!
            audio = sr.AudioData(wav_data, sample_rate=16000, sample_width=2)
            logger.info(f"Created AudioData: {len(wav_data)} bytes")

            # Try with the most basic approach first
            try:
                logger.info("Trying basic English recognition...")
                text = self.recognizer.recognize_google(audio, language="en-US", show_all=False)
                if text and text.strip():
                    logger.info(f"Basic English recognition successful: '{text}'")
                    return text, "en"
            except sr.UnknownValueError:
                logger.warning("Basic English recognition failed")
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {e}")

            # If basic fails, try other languages
            languages_to_try = ["en-IN", "te-IN", "hi-IN", "auto"]
            
            for lang in languages_to_try:
                try:
                    logger.info(f"Trying recognition with language: {lang}")
                    text = self.recognizer.recognize_google(audio, language=lang, show_all=False)
                    if text and text.strip():
                        logger.info(f"Recognition successful with language {lang}: '{text}'")
                        return text, lang
                    else:
                        logger.warning(f"Empty result with language {lang}")
                except sr.UnknownValueError:
                    logger.warning(f"Could not recognize speech with language {lang}")
                except sr.RequestError as e:
                    logger.error(f"Speech recognition service error with language {lang}: {e}")

            logger.warning("All speech recognition attempts failed")
            return "", "en"

        except Exception as e:
            logger.error(f"Speech to text error: {e}")
            return "", "en"

    def text_to_speech(self, text: str, language: str = "en") -> bytes:
        try:
            lang_mapping = {
                'te': 'te',
                'hi': 'hi',
                'en': 'en',
                'es': 'es',
                'fr': 'fr',
                'de': 'de',
            }
            tts_lang = lang_mapping.get(language, 'en')
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                tts.save(temp_file.name)
                with open(temp_file.name, 'rb') as f:
                    audio_bytes = f.read()
                os.unlink(temp_file.name)
                return audio_bytes
        except Exception as e:
            logger.error(f"Text to speech error: {e}")
            return b""

    def get_supported_languages(self) -> dict:
        return {
            "telugu": {
                "code": "te",
                "speech_recognition": "te-IN",
                "text_to_speech": "te",
                "display_name": "తెలుగు"
            },
            "hindi": {
                "code": "hi",
                "speech_recognition": "hi-IN",
                "text_to_speech": "hi",
                "display_name": "हिंदी"
            },
            "english": {
                "code": "en",
                "speech_recognition": "en-IN",
                "text_to_speech": "en",
                "display_name": "English"
            }
        }

    # In voice_utils_simple.py, inside the SimpleVoiceProcessor class

    def get_supported_audio_formats(self) -> List[str]:
        """
        Returns a list of commonly supported audio formats
        """
        return ["wav", "mp3", "ogg", "webm", "m4a", "mp4"]

    def speech_to_text_offline(self, audio_data: bytes) -> Tuple[str, str]:
        """
        Try offline speech recognition as fallback
        """
        try:
            audio_segment = self._convert_audio_to_segment(audio_data)
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                audio_segment.export(temp_wav.name, format='wav')
                temp_name = temp_wav.name

            with open(temp_name, 'rb') as wav_file:
                wav_data = wav_file.read()
            
            try:
                os.unlink(temp_name)
            except Exception:
                pass

            audio = sr.AudioData(wav_data[44:], sample_rate=16000, sample_width=2)
            
            # Try Sphinx offline recognition
            try:
                text = self.recognizer.recognize_sphinx(audio)
                logger.info(f"Offline recognition successful: '{text}'")
                return text, "en"
            except sr.UnknownValueError:
                logger.warning("Offline recognition failed")
                return "", "en"
            except Exception as e:
                logger.error(f"Offline recognition error: {e}")
                return "", "en"
                
        except Exception as e:
            logger.error(f"Offline speech to text error: {e}")
            return "", "en"

    def speech_to_text_whisper(self, audio_data: bytes) -> Tuple[str, str]:
        """
        Use OpenAI Whisper for speech recognition
        """
        try:
            logger.info("Trying Whisper speech recognition...")
            
            audio_segment = self._convert_audio_to_segment(audio_data)
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                audio_segment.export(temp_wav.name, format='wav')
                temp_name = temp_wav.name

            # Load Whisper model
            model = whisper.load_model("base")
            
            # Transcribe
            result = model.transcribe(temp_name)
            text = result["text"].strip()
            
            try:
                os.unlink(temp_name)
            except Exception:
                pass
            
            if text:
                logger.info(f"Whisper recognition successful: '{text}'")
                return text, "en"
            else:
                logger.warning("Whisper recognition returned empty text")
                return "", "en"
                
        except Exception as e:
            logger.error(f"Whisper speech to text error: {e}")
            return "", "en"

# Create global
voice_processor = SimpleVoiceProcessor()
