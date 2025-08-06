from deep_translator import GoogleTranslator
import re


def detect_language(text: str) -> str:
    """
    Enhanced language detection with better support for Indian languages
    """
    try:
        # First, try to detect Telugu specifically using Unicode ranges
        if contains_telugu(text):
            return 'te'

        # Try to detect Hindi specifically
        if contains_hindi(text):
            return 'hi'

        # Fall back to Google Translator detection
        detected = GoogleTranslator(source='auto', target='en').detect(text)

        # Map common language codes to ensure consistency
        language_mapping = {
            'te': 'te',  # Telugu
            'hi': 'hi',  # Hindi
            'en': 'en',  # English
            'es': 'es',  # Spanish
            'fr': 'fr',  # French
            'de': 'de',  # German
        }
        return language_mapping.get(detected, detected)
    except Exception as e:
        print(f"Language detection error: {e}")
        # Fallback: check for Telugu characters
        if contains_telugu(text):
            return 'te'
        return 'en'


def contains_telugu(text: str) -> bool:
    """
    Check if text contains Telugu characters using Unicode ranges
    """
    # Telugu Unicode range: 0C00-0C7F
    telugu_pattern = re.compile(r'[\u0C00-\u0C7F]')
    return bool(telugu_pattern.search(text))


def contains_hindi(text: str) -> bool:
    """
    Check if text contains Hindi/Devanagari characters using Unicode ranges
    """
    # Devanagari Unicode range: 0900-097F
    hindi_pattern = re.compile(r'[\u0900-\u097F]')
    return bool(hindi_pattern.search(text))


def translate_to_english(text: str) -> str:
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails


def translate_to_local(text: str, target_lang: str) -> str:
    try:
        # Ensure we have a valid target language code
        if target_lang == 'en':
            return text

        # Map language codes to Google Translate codes
        lang_mapping = {
            'te': 'te',  # Telugu
            'hi': 'hi',  # Hindi
            'es': 'es',  # Spanish
            'fr': 'fr',  # French
            'de': 'de',  # German
        }

        target_code = lang_mapping.get(target_lang, target_lang)
        return GoogleTranslator(source='en', target=target_code).translate(text)
    except Exception as e:
        print(f"Translation error to {target_lang}: {e}")
        return text  # Return original text if translation fails
