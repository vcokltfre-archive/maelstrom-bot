from os import getenv
from traceback import format_exc

from loguru import logger
from discord.ext import commands
from discord import Intents, Message, AllowedMentions

from .context import Context

from src.api.client import APIClient
from src.api.ws import WSClient


class Bot(commands.Bot):
    """A subclass of commands.Bot with additional functionality."""

    def __init__(self, *args, **kwargs):
        logger.info("Starting up...")

        intents = Intents.all()

        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            allowed_mentions=AllowedMentions(roles=False, everyone=False),
            *args,
            **kwargs
        )

        self.api: APIClient = None
        self.api_ws: WSClient = None

    def add_cog(self, cog) -> None:
        """Add a cog to the bot. Does not add disabled cogs."""

        if not hasattr(cog, "enabled") or cog.enabled:
            logger.info(f"Loading cog {cog.qualified_name}")
            return super().add_cog(cog)
        logger.info(f"Not loading cog {cog.qualified_name}")

    def load_extensions(self, *exts) -> None:
        """Load a given set of extensions."""

        logger.info(f"Starting loading {len(exts)} extensions...")

        success = 0

        for ext in exts:
            try:
                self.load_extension(ext)
            except Exception as e:
                logger.error(f"Error while loading {ext}: {e}:\n{format_exc()}")
            else:
                logger.info(f"Successfully loaded extension {ext}.")
                success += 1

        logger.info(f"Extension loading finished. Success: {success}. Failed: {len(exts) - success}.")

    async def login(self, *args, **kwargs) -> None:
        """Create the APIClient before login."""
        logger.info("Logging in to Discord...")

        self.api = APIClient(getenv("API_URL"), getenv("API_TOKEN"))
        await self.api.setup()

        self.api_ws = WSClient(self.api, self)
        self.loop.create_task(self.api_ws.stayalive())

        await super().login(*args, **kwargs)

    async def get_prefix(self, message: Message):
        """Get a dynamic prefix."""

        return "!"

    async def get_context(self, message: Message):
        """Get the context with the custom context class."""

        return await super().get_context(message, cls=Context)

    async def on_connect(self):
        """Log the connect event."""

        logger.info("Connected to Discord.")
