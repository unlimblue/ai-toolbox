"""Hub Listener - Monitors all Discord channels."""

import asyncio
import logging
from datetime import datetime
from typing import Callable, Optional

import discord

from .models import UnifiedMessage
from .config import (
    DISCORD_ID_TO_BOT_ID,
    ROLE_ID_TO_BOT_ID,
    DEBUG_MODE,
    DEBUG_CHANNEL_ID,
    DEBUG_AUTHOR_ID,
    DEBUG_PREFIX,
)

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
        
        # Debug mode setup
        self.debug_mode = DEBUG_MODE
        self.debug_channel_id = DEBUG_CHANNEL_ID
        self._debug_channel: Optional[discord.TextChannel] = None
    
    async def _get_debug_channel(self) -> Optional[discord.TextChannel]:
        """Get debug channel for logging."""
        if not self.debug_mode or not self.debug_channel_id:
            return None
        
        if self._debug_channel is None:
            self._debug_channel = self.client.get_channel(int(self.debug_channel_id))
        
        return self._debug_channel
    
    async def send_debug_message(self, content: str, extra_data: dict = None):
        """
        Send debug message to debug channel.
        
        Args:
            content: Debug message content
            extra_data: Additional data to include (msg_id, mentions, etc.)
        """
        if not self.debug_mode:
            return
        
        channel = await self._get_debug_channel()
        if not channel:
            return
        
        # Format debug message with timestamp
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        debug_msg = f"{DEBUG_PREFIX} [{timestamp}] {content}"
        
        # Add extra data if provided
        if extra_data:
            debug_msg += f"\n  📋 Data: {extra_data}"
        
        try:
            await channel.send(debug_msg)
            logger.debug(f"Debug message sent: {content[:50]}...")
        except Exception as e:
            logger.error(f"Failed to send debug message: {e}")
    
    def _setup_event_handlers(self):
        """Setup Discord event handlers."""
        
        @self.client.event
        async def on_ready():
            """Called when bot is ready."""
            logger.info(f"Hub Bot logged in as {self.client.user}")
            logger.info(f"Monitoring {len(self.client.guilds)} guild(s)")
            
            # Send debug message about startup
            if self.debug_mode:
                await self.send_debug_message(
                    "🚀 Hub Bot Started",
                    {"user": str(self.client.user), "guilds": len(self.client.guilds)}
                )
            
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
            
            # Ignore debug messages (prevent loop)
            if str(message.author.id) == DEBUG_AUTHOR_ID:
                return
            
            # Ignore other bots (optional, can be configured)
            if message.author.bot:
                logger.debug(f"Ignoring bot message from {message.author.name}")
                return
            
            try:
                # Debug: Log received message
                if self.debug_mode:
                    mentions_list = [f"@{m.name}" for m in message.mentions]
                    await self.send_debug_message(
                        "📨 Message Received",
                        {
                            "id": str(message.id),
                            "author": message.author.name,
                            "content": message.content[:100],
                            "channel": message.channel.name,
                            "mentions": mentions_list,
                            "is_bot": message.author.bot
                        }
                    )
                
                logger.info(f"📨 Received message from {message.author.name} in #{message.channel.name}: {message.content[:50]}...")
                await self.on_message_callback(message)
                
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                if self.debug_mode:
                    await self.send_debug_message(
                        f"❌ Error processing message: {str(e)}",
                        {"error_type": type(e).__name__}
                    )
                if self.on_error_callback:
                    await self.on_error_callback(e)
        
        @self.client.event
        async def on_error(event, *args, **kwargs):
            """Called when an error occurs."""
            logger.error(f"Discord client error in {event}: {args}, {kwargs}")
            if self.debug_mode:
                await self.send_debug_message(
                    f"❌ Discord Error in {event}",
                    {"args": str(args), "kwargs": str(kwargs)}
                )
    
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
        
        # Send debug message about shutdown
        if self.debug_mode:
            await self.send_debug_message("🛑 Hub Bot Stopping")
        
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
    # Extract mentions (convert Discord ID to bot_id)
    mentions = []
    
    # Check user mentions
    for mention in message.mentions:
        discord_id = str(mention.id)
        if discord_id in DISCORD_ID_TO_BOT_ID:
            mentions.append(DISCORD_ID_TO_BOT_ID[discord_id])
        elif mention.bot:
            # Fallback: use Discord ID directly if bot but not in mapping
            mentions.append(discord_id)
    
    # Check role mentions
    for role in message.role_mentions:
        role_id = str(role.id)
        if role_id in ROLE_ID_TO_BOT_ID:
            mentions.append(ROLE_ID_TO_BOT_ID[role_id])
    
    return UnifiedMessage(
        id=str(message.id),
        author_id=str(message.author.id),
        author_name=message.author.display_name,
        content=message.content,
        channel_id=str(message.channel.id),
        timestamp=message.created_at,
        mentions=mentions
    )
