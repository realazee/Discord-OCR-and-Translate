from __future__ import annotations

import logging

from deep_translator import GoogleTranslator

log = logging.getLogger(__name__)


def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """
    Translate a single string.

    Args:
        text: The text to translate.
        target_lang: Target language code (e.g. 'en', 'ja', 'es').
        source_lang: Source language code, or 'auto' for auto-detection.

    Returns:
        Translated string.
    """
    if not text.strip():
        return text
    try:
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        return translated or text
    except Exception:
        log.exception("Translation failed for text: %s", text[:50])
        return text


def translate_batch(texts: list[str], target_lang: str, source_lang: str = "auto") -> list[str]:
    """
    Translate a list of strings.

    Args:
        texts: List of strings to translate.
        target_lang: Target language code.
        source_lang: Source language code, or 'auto' for auto-detection.

    Returns:
        List of translated strings, in the same order.
    """
    if not texts:
        return []

    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        results = translator.translate_batch(texts)
        # Ensure we return original text if translation returned None
        return [r if r else t for r, t in zip(results, texts)]
    except Exception:
        log.exception("Batch translation failed, falling back to individual translations")
        return [translate_text(t, target_lang, source_lang) for t in texts]
