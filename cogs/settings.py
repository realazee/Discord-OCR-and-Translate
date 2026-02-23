from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.user_prefs import get_lang, set_lang

log = logging.getLogger(__name__)


class SettingsCog(commands.Cog):
    """Cog for managing user translation preferences."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="setlang", description="Set your preferred translation target language")
    @app_commands.describe(language="The language to translate images into")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def setlang(self, interaction: discord.Interaction, language: str) -> None:
        """Set the user's preferred target language."""
        # Build case-insensitive lookup maps
        valid_codes = {code.lower(): code for code in config.SUPPORTED_LANGUAGES.values()}
        valid_names = {name.lower(): code for name, code in config.SUPPORTED_LANGUAGES.items()}

        input_lower = language.strip().lower()

        # 1. Exact match on code (case-insensitive): "zh-CN", "zh-cn", "en"
        if input_lower in valid_codes:
            lang_code = valid_codes[input_lower]
        # 2. Exact match on name (case-insensitive): "Chinese (Simplified)"
        elif input_lower in valid_names:
            lang_code = valid_names[input_lower]
        else:
            # 3. Partial match on name: "chinese", "chin", etc.
            matches = [
                (name, code) for name, code in config.SUPPORTED_LANGUAGES.items()
                if input_lower in name.lower()
            ]
            if matches:
                lang_code = matches[0][1]
            else:
                lang_list = ", ".join(
                    f"`{name}` (`{code}`)" for name, code in sorted(config.SUPPORTED_LANGUAGES.items())
                )
                await interaction.response.send_message(
                    f"❌ Unknown language: `{language}`\n\n"
                    f"**Supported languages:**\n{lang_list}",
                    ephemeral=True,
                )
                return

        set_lang(interaction.user.id, lang_code)

        # Find the display name for the code
        display_name = next(
            (name for name, code in config.SUPPORTED_LANGUAGES.items() if code == lang_code),
            lang_code,
        )

        await interaction.response.send_message(
            f"✅ Translation language set to **{display_name}** (`{lang_code}`).\n"
            f"Future image translations will use this language.",
            ephemeral=True,
        )

    @setlang.autocomplete("language")
    async def language_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Provide autocomplete suggestions for the language parameter."""
        choices = []
        current_lower = current.lower()
        for name, code in sorted(config.SUPPORTED_LANGUAGES.items()):
            if current_lower in name.lower() or current_lower in code.lower():
                choices.append(app_commands.Choice(name=f"{name} ({code})", value=code))
            if len(choices) >= 25:  # Discord limit
                break
        return choices

    @app_commands.command(name="currentlang", description="Check your current translation target language")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def currentlang(self, interaction: discord.Interaction) -> None:
        """Show the user's current target language."""
        lang_code = get_lang(interaction.user.id)
        display_name = next(
            (name for name, code in config.SUPPORTED_LANGUAGES.items() if code == lang_code),
            lang_code,
        )
        await interaction.response.send_message(
            f"🌐 Your current translation language is **{display_name}** (`{lang_code}`).\n"
            f"Use `/setlang` to change it.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SettingsCog(bot))
