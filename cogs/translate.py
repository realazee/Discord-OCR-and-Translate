from __future__ import annotations

import logging
from io import BytesIO

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from utils.image_edit import render_translated_image
from utils.ocr import detect_text
from utils.translator import translate_batch
from utils.user_prefs import get_lang

log = logging.getLogger(__name__)

# Supported image MIME types
IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}


class TranslateCog(commands.Cog):
    """Cog for the image translation context menu command."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Create the context menu command
        self.translate_ctx_menu = app_commands.ContextMenu(
            name="Translate Image",
            callback=self._translate_image_callback,
            allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
            allowed_contexts=app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
        )
        self.bot.tree.add_command(self.translate_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.translate_ctx_menu.name, type=self.translate_ctx_menu.type
        )

    async def _find_image_url(self, message: discord.Message) -> str | None:
        """Extract the first image URL from a message's attachments or embeds."""
        # Check attachments first
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.split(";")[0] in IMAGE_TYPES:
                return attachment.url
            # Fallback: check by file extension
            if any(attachment.filename.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp")):
                return attachment.url

        # Check embeds for images
        for embed in message.embeds:
            if embed.image and embed.image.url:
                return embed.image.url
            if embed.thumbnail and embed.thumbnail.url:
                return embed.thumbnail.url

        return None

    async def _download_image(self, url: str) -> bytes:
        """Download an image from a URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise ValueError(f"Failed to download image (HTTP {resp.status})")
                return await resp.read()

    async def _translate_image_callback(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        """Context menu handler: translate text in an image."""
        await interaction.response.defer(thinking=True)

        try:
            # 1. Find an image in the message
            image_url = await self._find_image_url(message)
            if not image_url:
                await interaction.followup.send(
                    "❌ No image found in that message. "
                    "Right-click a message that contains an image.",
                    ephemeral=True,
                )
                return

            # 2. Download the image
            try:
                image_bytes = await self._download_image(image_url)
            except Exception:
                log.exception("Failed to download image")
                await interaction.followup.send(
                    "❌ Failed to download the image. Please try again.",
                    ephemeral=True,
                )
                return

            # 3. OCR — detect text regions (CPU-bound, run in executor)
            loop = self.bot.loop
            regions, detected_script = await loop.run_in_executor(None, detect_text, image_bytes)

            if not regions:
                await interaction.followup.send(
                    "🔍 No text was detected in that image.",
                    ephemeral=True,
                )
                return

            # 4. Get user's target language
            target_lang = get_lang(interaction.user.id)

            # 5. Translate all detected text
            original_texts = [r.text for r in regions]
            translated_texts = await loop.run_in_executor(
                None, translate_batch, original_texts, target_lang
            )

            # 6. Render translated text onto image (CPU-bound)
            result_bytes = await loop.run_in_executor(
                None, render_translated_image, image_bytes, regions, translated_texts
            )

            # 7. Send the result
            file = discord.File(BytesIO(result_bytes), filename="translated.png")

            # Build a summary of what was translated
            summary_lines = []
            for orig, trans in zip(original_texts, translated_texts):
                if orig.strip() != trans.strip():
                    summary_lines.append(f"• *\"{orig}\"* → **\"{trans}\"**")

            summary = "\n".join(summary_lines[:10])  # Cap at 10 lines
            if len(summary_lines) > 10:
                summary += f"\n... and {len(summary_lines) - 10} more"

            content = (
                f"🌐 **Detected: `{detected_script}`** → **Translated to: `{target_lang}`** "
                f"({len(regions)} text region(s) found)\n{summary}"
            )

            await interaction.followup.send(content=content, file=file)

        except Exception:
            log.exception("Error in translate_image_callback")
            await interaction.followup.send(
                "❌ An error occurred while processing the image. Please try again.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TranslateCog(bot))
