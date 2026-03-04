"""Role Bot - Individual bot with specific persona and capabilities."""

import asyncio
import logging
import os
from typing import List, Optional

import discord

from ..providers import create_provider
from ..providers.base import ChatMessage
from .models import UnifiedMessage, CrossChannelTask, BotState, BotConfig
from .context_filter import ContextFilter, RelevanceScorer

logger = logging.getLogger(__name__)


class RoleBot:
    """
    Role Bot with specific persona and channel permissions.
    
    Features:
    - Responds to messages in allowed channels
    - Manages conversation context
    - Handles cross-channel tasks
    """
    
    def __init__(self, config: BotConfig):
        """
        Initialize Role Bot.
        
        Args:
            config: BotConfig with persona and settings
        """
        self.config = config
        self.bot_id = config.bot_id
        self.state = BotState.IDLE
        self.current_task: Optional[CrossChannelTask] = None
        self.max_context = 15
        
        # Context management
        self.context_filter = ContextFilter(bot_id=self.bot_id, max_context=self.max_context)
        self.relevance_scorer = RelevanceScorer(bot_id=self.bot_id)
        
        # Discord client (for sending messages)
        self._client: Optional[discord.Client] = None
        self._connected = False
        
        # Get token from environment
        self.token = os.getenv(config.token_env)
        if not self.token:
            logger.warning(f"Token not found for bot {config.bot_id}: {config.token_env}")
    
    async def connect(self):
        """Connect to Discord (for sending messages)."""
        if self._connected:
            return
        
        if not self.token:
            raise ValueError(f"No token available for bot {self.bot_id}")
        
        self._client = discord.Client(intents=discord.Intents.default())
        await self._client.login(self.token)
        self._connected = True
        logger.info(f"Bot {self.bot_id} connected to Discord")
    
    async def disconnect(self):
        """Disconnect from Discord."""
        if self._client and self._connected:
            await self._client.close()
            self._connected = False
            logger.info(f"Bot {self.bot_id} disconnected")
    
    async def handle_message(self, message: UnifiedMessage):
        """
        Handle incoming message.
        
        Args:
            message: UnifiedMessage to process
        """
        # Update context if relevant
        added = self.context_filter.add_message(message)
        if added:
            logger.debug(f"Bot {self.bot_id} added message to context")
        
        # Handle based on state
        if self.state == BotState.DISCUSSING and self.current_task:
            self._check_conclusion(message)
        
        # Generate response if needed
        if self._should_respond(message):
            response = await self._generate_response(message)
            if response:
                await self.send_message(message.channel_id, response)
    
    async def handle_task(self, task: CrossChannelTask):
        """
        Handle cross-channel task.
        
        Args:
            task: CrossChannelTask to handle
        """
        self.state = BotState.DISCUSSING
        self.current_task = task
        
        logger.info(f"Bot {self.bot_id} handling task: {task.task_id}")
        
        # Confirm in source channel
        await self.send_message(
            task.source_channel,
            "领旨，即刻去内阁商议。"
        )
        
        # Start in target channel
        await self.send_message(
            task.target_channel,
            f"奉陛下旨意，来此商议：{task.instruction}"
        )
    
    def _is_relevant(self, message: UnifiedMessage) -> bool:
        """Check if message is relevant to this bot."""
        return self.context_filter._is_relevant(message)
    
    def _should_respond(self, message: UnifiedMessage) -> bool:
        """Determine if bot should respond to message."""
        # Don't respond to own messages
        if message.author_id == self.bot_id:
            return False
        
        # Respond if mentioned
        if self.bot_id in message.mentions:
            return True
        
        return False
    
    def _check_conclusion(self, message: UnifiedMessage):
        """Check if discussion should conclude."""
        if not self.current_task:
            return

        # Trigger conditions
        trigger_words = ["结论", "定论", "结果", "就这样", "同意"]
        has_trigger = any(word in message.content for word in trigger_words)

        # Discussion length
        discussion_length = len(self.context_filter.context)

        if has_trigger or discussion_length >= 10:
            logger.info(f"Bot {self.bot_id} triggering conclusion")
            asyncio.create_task(self._form_conclusion())
    
    async def _generate_response(self, message: UnifiedMessage) -> Optional[str]:
        """Generate AI response."""
        try:
            # Build context using context filter
            context_text = self.context_filter.get_context_for_prompt(limit=10)
            
            # Build prompt
            prompt = f"""相关对话：
{context_text}

{message.author_name}：{message.content}

请回复："""
            
            # Call AI
            api_key = os.getenv(self.config.api_key_env)
            if not api_key:
                logger.error(f"API key not found: {self.config.api_key_env}")
                return None
            
            client = create_provider(
                self.config.model_provider,
                api_key=api_key,
                model=self.config.model_name
            )
            
            messages = [
                ChatMessage(role="system", content=self.config.persona.system_prompt),
                ChatMessage(role="user", content=prompt)
            ]
            
            response = await client.chat(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None
    
    async def _form_conclusion(self):
        """Form conclusion and report back."""
        if not self.current_task:
            return
        
        self.state = BotState.REPORTING
        
        try:
            # Generate conclusion using context
            discussion = self.context_filter.get_context_for_prompt(limit=20)
            
            prompt = f"""基于以下讨论，形成简洁结论：

讨论记录：
{discussion}

请用一句话总结结论："""
            
            api_key = os.getenv(self.config.api_key_env)
            client = create_provider(
                self.config.model_provider,
                api_key=api_key,
                model=self.config.model_name
            )
            
            messages = [ChatMessage(role="user", content=prompt)]
            response = await client.chat(messages)
            conclusion = response.content
            
            # Report back to source channel
            await self.send_message(
                self.current_task.source_channel,
                f"启禀陛下，臣等已在内阁商议完毕。\n\n结论：{conclusion}"
            )
            
        except Exception as e:
            logger.error(f"Error forming conclusion: {e}")
        
        finally:
            # Reset state
            self.state = BotState.IDLE
            self.current_task = None
            self.context_filter.clear()
    
    async def send_message(self, channel_id: str, content: str):
        """
        Send message to channel.
        
        Args:
            channel_id: Discord channel ID
            content: Message content
        """
        if not self._connected:
            await self.connect()
        
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                await channel.send(content)
                logger.debug(f"Bot {self.bot_id} sent message to {channel_id}")
            else:
                logger.warning(f"Channel not found: {channel_id}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
