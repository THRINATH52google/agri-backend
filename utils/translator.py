from deep_translator import GoogleTranslator

def detect_language(text: str) -> str:
    try:
        return GoogleTranslator(source='auto', target='en').detect(text)
    except Exception:
        return 'en'

def translate_to_english(text: str) -> str:
    return GoogleTranslator(source='auto', target='en').translate(text)

def translate_to_local(text: str, target_lang: str) -> str:
    return GoogleTranslator(source='en', target=target_lang).translate(text)
