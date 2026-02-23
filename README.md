# Discord OCR & Translate Bot

A Discord bot that translates text on images in-place. Right-click any message with an image, select **Apps → Translate Image**, and get back the same image with translated text overlaid — similar to how Google Translate's camera mode works.

Works as both a **user-installable app** (use it anywhere, even in servers where it's not added) and a **server app**.

## Features

- **Right-click context menu** — Translate images directly from the Apps menu
- **80+ source languages** — Auto-detects the language on the image via EasyOCR
- **35+ target languages** — Set your preferred language with `/setlang`
- **In-place replacement** — Original text is replaced with translated text on the image
- **User + Server install** — Install to your account or to a server

## Prerequisites

- **Python 3.10+**
- A **Discord Bot Token** from the [Discord Developer Portal](https://discord.com/developers/applications)

## Discord Developer Portal Setup

1. Create a new application at the [Discord Developer Portal](https://discord.com/developers/applications)
2. Go to **Installation** → set **Installation Contexts** to both **Guild Install** and **User Install**
3. Under **Guild Install**, set default scopes to `bot` and `applications.commands`
4. Under **User Install**, set default scopes to `applications.commands`
5. Go to **Bot** → enable **Message Content Intent**
6. Copy your bot **Token**

## Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/Discord-OCR-and-Translate.git
cd Discord-OCR-and-Translate

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure your token
cp .env.example .env
# Edit .env and add your bot token
```

## Running

```bash
python bot.py
```

The bot will log `Bot is ready!` and sync its commands. The first time you translate an image, EasyOCR will download its language models (~100MB) which may take a minute.

## Usage

### Translate an Image
1. Find a message with an image in Discord
2. **Right-click** the message (or long-press on mobile)
3. Go to **Apps → Translate Image**
4. The bot replies with the translated image and a summary

### Set Your Language
```
/setlang language:Japanese
```
Supports autocomplete — start typing a language name to see suggestions.

### Check Current Language
```
/currentlang
```

## Project Structure

```
├── bot.py              # Entry point — bot setup & cog loader
├── config.py           # Environment & language configuration
├── cogs/
│   ├── translate.py    # Context menu command & image pipeline
│   └── settings.py     # /setlang and /currentlang commands
├── utils/
│   ├── ocr.py          # EasyOCR text detection wrapper
│   ├── translator.py   # Google Translate wrapper
│   ├── image_edit.py   # Image inpainting & text rendering
│   └── user_prefs.py   # Per-user language preferences (JSON)
└── data/               # Runtime data (auto-created)
    └── user_prefs.json
```

## Optional: Better Font Support

For best results with CJK and other non-Latin scripts, place font files in a `fonts/` directory:

```
fonts/
├── NotoSans-Regular.ttf
└── NotoSansCJKsc-Regular.otf
```

You can download [Noto Sans](https://fonts.google.com/noto/specimen/Noto+Sans) from Google Fonts.
Without custom fonts, the bot will use system fonts or Pillow's default.
