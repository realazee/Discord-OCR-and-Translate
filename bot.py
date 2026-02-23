import asyncio
import logging
import os

import discord
from discord.ext import commands

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("bot")


class TranslateBot(commands.Bot):
    """Discord bot for OCR-based image translation."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            allowed_installs=discord.app_commands.AppInstallationType(
                guild=True,
                user=True,
            ),
            allowed_contexts=discord.app_commands.AppCommandContext(
                guild=True,
                dm_channel=True,
                private_channel=True,
            ),
        )

    async def setup_hook(self) -> None:
        """Load all cogs from the cogs/ directory."""
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    log.info("Loaded cog: %s", cog_name)
                except Exception:
                    log.exception("Failed to load cog: %s", cog_name)

    async def on_ready(self) -> None:
        log.info("Bot is ready! Logged in as %s (ID: %s)", self.user, self.user.id)
        synced = await self.tree.sync()
        log.info("Synced %d command(s)", len(synced))


async def main() -> None:
    if not config.DISCORD_TOKEN:
        log.error("DISCORD_TOKEN not set. Copy .env.example to .env and add your token.")
        return

    bot = TranslateBot()
    async with bot:
        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
