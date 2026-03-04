"""Hub Listener - Monitors all Discord channels."""

import asyncio
import logging
from typing import Callable, Optional

import discord

from .models import UnifiedMessage

logger = logging.getLogger(__name__)


class HubListener:
    """
    Hub Bot that listens to all channels and forwards messages to MessageBus.
    
    Uses Hub Token for authentication and requires read permissions for all channels.
    """
    
    def __init__(
        self,
        token: str,
        on_message: Callable[[discord.Message], None],
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        """
        Initialize Hub Listener.
        
        Args:
            token: Discord Bot Token for Hub
            on_message: Callback function for new messages
            on_error: Optional callback for error handling
        """
        self.token = token
        self.on_message_callback = on_message
        self.on_error_callback = on_error
        self.client = discord.Client(intents=discord.Intents.all())
        self._setup_event_handlers()
        self._running = False
    
    def _setup_event_handlers(self):
        """Setup Discord event handlers."""
        
        @self.client.event
        async def on_ready():
            """Called when bot is ready."""
            logger.info(f"Hub Bot logged in as {self.client.user}")
            logger.info(f"Monitoring {len(self.client.guilds)} guild(s)")
            for guild in self.client.guilds:
                logger.info(f"  - {guild.name} ({guild.id})")
                channels = [c.name for c in guild.channels if isinstance(c, discord.TextChannel)]
                logger.info(f"    Channels: {', '.join(channels)}")
        
        @self.client.event
        async def on_message(message: discord.Message):
            """Called when a message is received."""
            # Ignore own messages
            if message.author.id == self.client.user.id:
                return
            
            # Ignore other bots (optional, can be configured)
            if message.author.bot:
                logger.debug(f"Ignoring bot message from {message.author.name}")
                return
            
            try:
                logger.debug(f"Received message from {message.author.name} in #{message.channel.name}")
                await self.on_message_callback(message)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if self.on_error_callback:
                    await self.on_error_callback(e)
        
        @self.client.event
        async def on_error(event, *args, **kwargs):
            """Called when an error occurs."""
            logger.error(f"Discord client error in {event}: {args}, {kwargs}")
    
    async def start(self):
        """Start the Hub Listener."""
        if self._running:
            logger.warning("Hub Listener already running")
            return
        
        logger.info("Starting Hub Listener...")
        self._running = True
        
        try:
            await self.client.start(self.token)
        except Exception as e:
            logger.error(f"Failed to start Hub Listener: {e}")
            self._running = False
            raise
    
    async def stop(self):
        """Stop the Hub Listener gracefully."""
        if not self._running:
            return
        
        logger.info("Stopping Hub Listener...")
        self._running = False
        await self.client.close()
    
    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running and not self.client.is_closed()


def discord_message_to_unified(message: discord.Message) -> UnifiedMessage:
    """
    Convert Discord message to UnifiedMessage format.
    
    Args:
        message: Discord message object
        
    Returns:
        UnifiedMessage
    """
    # Extract mentions (bot mentions only)
    mentions = []
    for mention in message.mentions:
        # Check if mention is a bot (simplified logic)
        if mention.bot:
            mentions.append(str(mention.id))
    
    # Also check role mentions if needed
    # for role in message.role_mentions:
    #     mentions.append(f"role_{role.id}")
    
    return UnifiedMessage(
        id=str(message.id),
        author_id=str(message.author.id),
        author_name=message.author.display_name,
        content=message.content,
        channel_id=str(message.channel.id),
        timestamp=message.created_at,
        mentions=mentions
    )
