import logging
from langdetect import detect
from deep_translator import GoogleTranslator
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "english",
    "hi": "hindi",
    "ta": "tamil",
    "te": "telugu",
    "kn": "kannada",
    "ml": "malayalam",
    "mr": "marathi",
    "gu": "gujarati",
    "pa": "punjabi",
    "bn": "bengali",
    "or": "odia"
}

def detect_language(text: str) -> str:
    """
    Detect language of input text. Fallback to English if unable to detect or unsupported.
    """
    if not text or len(text.strip()) < 3:
        return "en"
    try:
        lang = detect(text)
        if lang in SUPPORTED_LANGUAGES:
            return lang
        return "en"
    except Exception as e:
        logger.warning(f"Language detection failed: {e}. Defaulting to English ('en').")
        return "en"

def translate_to_english(text: str, source_lang: str) -> Tuple[str, str]:
    """
    Translates text to English if it is not already in English.
    Returns: (translated_text, source_lang)
    """
    if not text or text.strip() == "":
        return "", source_lang

    if source_lang == "en":
        return text, "en"

    try:
        translated = GoogleTranslator(source=source_lang, target="en").translate(text)
        return translated, source_lang
    except Exception as e:
        logger.error(f"Translation to English failed for source language {source_lang}: {e}")
        # Fallback to general auto-detect translation
        try:
            translated = GoogleTranslator(source="auto", target="en").translate(text)
            return translated, source_lang
        except Exception:
            return text, source_lang

def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translates text from English to the target language.
    """
    if not text or text.strip() == "" or target_lang == "en":
        return text

    try:
        translated = GoogleTranslator(source="en", target=target_lang).translate(text)
        return translated
    except Exception as e:
        logger.error(f"Translation from English to {target_lang} failed: {e}")
        return text
