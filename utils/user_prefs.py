from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import config

log = logging.getLogger(__name__)

_DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"
_PREFS_FILE = _DATA_DIR / "user_prefs.json"


def _load_prefs() -> dict:
    """Load user preferences from disk."""
    if _PREFS_FILE.exists():
        try:
            with open(_PREFS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            log.warning("Could not read preferences file, starting fresh.")
    return {}


def _save_prefs(prefs: dict) -> None:
    """Save user preferences to disk."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)


def get_lang(user_id: int) -> str:
    """
    Get a user's preferred target language.

    Returns the language code (e.g. 'en') or the default from config.
    """
    prefs = _load_prefs()
    return prefs.get(str(user_id), config.DEFAULT_LANGUAGE)


def set_lang(user_id: int, lang: str) -> None:
    """
    Set a user's preferred target language.

    Args:
        user_id: The Discord user ID.
        lang: Target language code (e.g. 'ja', 'es').
    """
    prefs = _load_prefs()
    prefs[str(user_id)] = lang
    _save_prefs(prefs)
    log.info("Set language for user %d to %s", user_id, lang)
