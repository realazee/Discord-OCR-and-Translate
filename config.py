import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEFAULT_LANGUAGE = "en"

# Supported languages for the /setlang autocomplete
SUPPORTED_LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese (Simplified)": "zh-CN",
    "Chinese (Traditional)": "zh-TW",
    "Arabic": "ar",
    "Hindi": "hi",
    "Turkish": "tr",
    "Vietnamese": "vi",
    "Thai": "th",
    "Indonesian": "id",
    "Dutch": "nl",
    "Polish": "pl",
    "Ukrainian": "uk",
    "Czech": "cs",
    "Swedish": "sv",
    "Danish": "da",
    "Finnish": "fi",
    "Norwegian": "no",
    "Hungarian": "hu",
    "Romanian": "ro",
    "Greek": "el",
    "Hebrew": "he",
    "Malay": "ms",
    "Filipino": "tl",
    "Bengali": "bn",
    "Tamil": "ta",
    "Telugu": "te",
    "Urdu": "ur",
    "Persian": "fa",
}
