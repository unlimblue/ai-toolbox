"""Role Bot - Individual bot with specific persona and capabilities."""

import asyncio
import logging
import os
from typing import List, Optional, Callable, Dict
from datetime import datetime, timedelta

import discord

from ..providers import create_provider
from ..providers.base import ChatMessage
from .models import UnifiedMessage, CrossChannelTask, BotState, BotConfig
from .context_filter import ContextFilter, RelevanceScorer
from .config_loader import get_config

logger = logging.getLogger(__name__)


class RoleBot:
    """
    Role Bot with specific persona and channel permissions.
    
    Features:
    - Responds to messages in allowed channels
    - Manages conversation context
    - Handles cross-channel tasks
    - Has system architecture awareness
    - Tracks conversation state for multi-turn dialogue
    """
    
    def __init__(self, config: BotConfig, architecture_info: Dict = None):
        """
        Initialize Role Bot.
        
        Args:
            config: BotConfig with persona and settings
            architecture_info: System architecture information for awareness
        """
        self.config = config
        self.bot_id = config.bot_id
        self.state = BotState.IDLE
        self.current_task: Optional[CrossChannelTask] = None
        self.max_context = 15
        
        # System architecture awareness
        self.architecture_info = architecture_info or {}
        self._parse_architecture_info()
        
        # Context management
        self.context_filter = ContextFilter(bot_id=self.bot_id, max_context=self.max_context)
        self.relevance_scorer = RelevanceScorer(bot_id=self.bot_id)
        
        # Conversation state tracking for multi-turn dialogue
        self.conversation_state = {
            "active": False,
            "started_at": None,
            "last_message_at": None,
            "partners": [],  # List of bot_ids we're conversing with
            "channel": None,
            "message_count": 0,
        }
        self.conversation_timeout = timedelta(minutes=10)
        
        # Discord client (for sending messages)
        self._client: Optional[discord.Client] = None
        self._connected = False
        
        # Debug sender
        self.debug_sender: Optional[Callable] = None
        
        # Get token from environment
        self.token = os.getenv(config.token_env)
        if not self.token:
            logger.warning(f"Token not found for bot {config.bot_id}: {config.token_env}")
    
    def _parse_architecture_info(self):
        """Parse architecture info for quick access."""
        self.my_user_id = self.architecture_info.get('bot_user_id')
        self.my_role_id = self.architecture_info.get('bot_role_id')
        self.my_name = self.architecture_info.get('bot_name', self.bot_id)
    
    def set_debug_sender(self, sender: Callable):
        """Set debug message sender callback."""
        self.debug_sender = sender
    
    async def _send_debug(self, content: str, data: dict = None):
        """Send debug message."""
        if self.debug_sender:
            try:
                await self.debug_sender(f"[{self.bot_id}] {content}", data)
            except Exception as e:
                logger.error(f"Failed to send debug message: {e}")
    
    # ==================== Conversation State Management ====================
    
    def _update_conversation_state(self, message: UnifiedMessage):
        """
        Update conversation state based on incoming message.
        
        Tracks:
        - Whether we're in an active conversation
        - Who we're talking to
        - When the conversation started/last had activity
        """
        now = datetime.now()
        
        # If bot is mentioned, activate or continue conversation
        if self.bot_id in message.mentions:
            self.conversation_state["active"] = True
            self.conversation_state["last_message_at"] = now
            self.conversation_state["channel"] = message.channel_id
            
            # Record conversation start time if not set
            if self.conversation_state["started_at"] is None:
                self.conversation_state["started_at"] = now
            
            # Track conversation partners
            for mention in message.mentions:
                if mention != self.bot_id and mention not in self.conversation_state["partners"]:
                    self.conversation_state["partners"].append(mention)
            
            # Also track the author if they're a bot
            config = get_config()
            if message.author_id in config.discord_config.get("user_id_to_bot", {}).values():
                author_bot_id = None
                for uid, bid in config.discord_config["user_id_to_bot"].items():
                    if bid == message.author_id:
                        author_bot_id = bid
                        break
                if author_bot_id and author_bot_id not in self.conversation_state["partners"]:
                    self.conversation_state["partners"].append(author_bot_id)
        
        # Check if conversation has timed out
        self._check_conversation_timeout()
    
    def _check_conversation_timeout(self) -> bool:
        """
        Check if conversation has timed out.
        
        Returns:
            True if conversation is still active, False if timed out
        """
        if not self.conversation_state["active"]:
            return False
        
        last_activity = self.conversation_state.get("last_message_at")
        if last_activity is None:
            return False
        
        if datetime.now() - last_activity > self.conversation_timeout:
            # Conversation timed out
            self._end_conversation()
            return False
        
        return True
    
    def _end_conversation(self):
        """End the current conversation."""
        logger.info(f"Bot {self.bot_id} ending conversation (timeout or completion)")
        self.conversation_state["active"] = False
        self.conversation_state["partners"] = []
        self.conversation_state["message_count"] = 0
        # Keep started_at for history, clear channel
        self.conversation_state["channel"] = None
    
    def _increment_message_count(self):
        """Increment conversation message count."""
        self.conversation_state["message_count"] = self.conversation_state.get("message_count", 0) + 1
    
    def _is_in_active_conversation(self) -> bool:
        """Check if bot is currently in an active conversation."""
        if not self.conversation_state["active"]:
            return False
        return self._check_conversation_timeout()
    
    def _is_conversation_partner(self, author_id: str) -> bool:
        """Check if author is a known conversation partner."""
        if not self.conversation_state["partners"]:
            return False
        
        # Check if author_id matches any partner's user_id
        config = get_config()
        for partner_id in self.conversation_state["partners"]:
            partner_user_id = config.get_user_id_for_bot(partner_id)
            if partner_user_id == author_id:
                return True
        
        return False
    
    # ==================== Mention Formatting ====================
    
    def format_mention(self, target_bot_id: str) -> str:
        """
        Format a mention for target bot.
        
        Args:
            target_bot_id: The bot_id to mention
            
        Returns:
            Discord mention format string
        """
        config = get_config()
        
        # Priority 1: Use role mention (if available)
        role_id = config.get_role_id_for_bot(target_bot_id)
        if role_id:
            return f"<@&{role_id}>"
        
        # Priority 2: Use user mention
        user_id = config.get_user_id_for_bot(target_bot_id)
        if user_id:
            return f"<@{user_id}>"
        
        # Fallback: Use name
        target_config = config.get_bot_config(target_bot_id)
        return f"@{target_config.get('name', target_bot_id)}"
    
    def format_message_with_mentions(self, content: str, mentions: List[str] = None) -> str:
        """
        Format message content with proper mentions.
        
        Args:
            content: Message content (can contain {bot_id} placeholders)
            mentions: List of bot_ids to mention
            
        Returns:
            Formatted message with Discord mention syntax
        """
        formatted = content
        
        # Replace {bot_id} placeholders with actual mentions
        if mentions:
            for bot_id in mentions:
                mention_str = self.format_mention(bot_id)
                placeholder = f"{{{bot_id}}}"
                formatted = formatted.replace(placeholder, mention_str)
        
        return formatted
    
    async def connect(self):
        """
        Connect to Discord and keep connection alive.
        This method blocks until the client is closed.
        """
        if self._connected:
            return
        
        if not self.token:
            raise ValueError(f"No token available for bot {self.bot_id}")
        
        self._client = discord.Client(intents=discord.Intents.default())
        
        # Setup on_ready event
        @self._client.event
        async def on_ready():
            logger.info(f"Bot {self.bot_id} logged in as {self._client.user}")
            await self._send_debug(
                f"🟢 Bot online: {self._client.user}",
                {"user_id": str(self._client.user.id)}
            )
        
        self._connected = True
        
        # Start the client (this blocks until disconnect)
        try:
            await self._client.start(self.token)
        except Exception as e:
            self._connected = False
            logger.error(f"Bot {self.bot_id} connection error: {e}")
            raise
    
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
        await self._send_debug(
            "📥 handle_message called",
            {
                "message_id": message.id,
                "author_id": message.author_id,
                "bot_id": self.bot_id,
                "mentions": message.mentions,
                "is_own_message": message.author_id == self.bot_id,
                "is_mentioned": self.bot_id in message.mentions
            }
        )
        
        # Update context if relevant
        added = self.context_filter.add_message(message)
        if added:
            logger.debug(f"Bot {self.bot_id} added message to context")
            await self._send_debug("📝 Message added to context")
        else:
            await self._send_debug("⏭️ Message not relevant, not added to context")
        
        # Handle based on state
        if self.state == BotState.DISCUSSING and self.current_task:
            await self._send_debug("🔍 Checking for conclusion trigger")
            self._check_conclusion(message)
        
        # Generate response if needed
        should_respond = self._should_respond(message)
        await self._send_debug(
            f"🤔 _should_respond returned: {should_respond}"
        )
        
        if should_respond:
            await self._send_debug("📝 Generating response...")
            response = await self._generate_response(message)
            if response:
                await self._send_debug(
                    "✅ Response generated, sending...",
                    {"response": response[:50]}
                )
                await self.send_message(message.channel_id, response)
                
                # Check if conversation should end (no mentions in response)
                has_mentions = '<@&' in response or '<@' in response
                if not has_mentions and self.conversation_state["active"]:
                    logger.info(f"🛑 Bot {self.bot_id} ending conversation (no mentions in response)")
                    await self._send_debug("🛑 Ending conversation (no mentions in response)")
                    self._end_conversation()
            else:
                await self._send_debug("❌ No response generated")
        else:
            await self._send_debug("⏭️ Not generating response")
    
    async def handle_task(self, task: CrossChannelTask):
        """
        Handle cross-channel task.
        
        Args:
            task: CrossChannelTask to handle
        """
        self.state = BotState.DISCUSSING
        self.current_task = task
        
        logger.info(f"🤖 Bot {self.bot_id} handling task: {task.task_id}")
        await self._send_debug(
            "🤖 Handling Task",
            {"task_id": task.task_id, "state": self.state.value}
        )
        
        # Ensure connected
        if not self._connected:
            logger.info(f"🔌 Bot {self.bot_id} connecting to Discord...")
            await self._send_debug("🔌 Connecting to Discord...")
            await self.connect()
        
        # Confirm in source channel
        logger.info(f"📤 Bot {self.bot_id} sending confirmation to source channel {task.source_channel}")
        await self._send_debug(
            "📤 Sending confirmation to source channel",
            {"channel": task.source_channel}
        )
        await self.send_message(
            task.source_channel,
            "领旨，即刻去内阁商议。"
        )
        
        # Start in target channel
        logger.info(f"📤 Bot {self.bot_id} sending start message to target channel {task.target_channel}")
        await self._send_debug(
            "📤 Sending start message to target channel",
            {"channel": task.target_channel}
        )
        await self.send_message(
            task.target_channel,
            f"奉陛下旨意，来此商议：{task.instruction}"
        )
    
    def _is_relevant(self, message: UnifiedMessage) -> bool:
        """Check if message is relevant to this bot."""
        return self.context_filter._is_relevant(message)
    
    def _should_respond(self, message: UnifiedMessage) -> bool:
        """
        Determine if bot should respond to message.
        
        Extended to support multi-turn conversation:
        - Always respond when mentioned
        - Continue responding during active conversation
        - Stop when conversation times out or completes
        """
        # Update conversation state first
        self._update_conversation_state(message)
        
        # Don't respond to own messages
        if message.author_id == self.bot_id:
            return False
        
        # Always respond if mentioned
        if self.bot_id in message.mentions:
            self._increment_message_count()
            return True
        
        # During active conversation, continue responding to partners
        if self._is_in_active_conversation():
            # Check if message is from a conversation partner
            if self._is_conversation_partner(message.author_id):
                self._increment_message_count()
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
            
            # Build prompt with anti-loop instruction
            prompt = f"""相关对话：
{context_text}

{message.author_name}：{message.content}

⚠️ 重要提醒：
- 如果你是被对方@了，回复时**不要@回去**，除非你需要对方回复
- 只有当你有问题或需要继续讨论时，才@对方
- 简单的回应、同意、确认，都不要@，避免无限循环

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
            logger.info(f"🔌 Bot {self.bot_id} not connected, connecting...")
            await self._send_debug("🔌 Not connected, connecting...")
            await self.connect()
        
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                # Log FULL message content for debugging
                logger.info(f"📤 Bot {self.bot_id} SENDING to {channel_id}: {content}")
                await self._send_debug(
                    "📤 SENDING message",
                    {"channel": channel_id, "content": content, "length": len(content)}
                )
                
                sent_message = await channel.send(content)
                
                # Log success with full content
                logger.info(f"✅ Bot {self.bot_id} SENT to {channel_id}: {content}")
                await self._send_debug(
                    "✅ SENT message",
                    {
                        "channel": channel_id, 
                        "content": content,
                        "message_id": str(sent_message.id),
                        "has_mentions": bool(sent_message.mentions) if hasattr(sent_message, 'mentions') else 'unknown'
                    }
                )
            else:
                logger.error(f"❌ Bot {self.bot_id}: Channel not found: {channel_id}")
                await self._send_debug(
                    "❌ Channel not found",
                    {"channel": channel_id}
                )
        except Exception as e:
            logger.error(f"❌ Bot {self.bot_id} error sending message: {e}")
            logger.error(f"   Failed content: {content[:200]}")
            await self._send_debug(
                "❌ Error sending message",
                {"channel": channel_id, "error": str(e), "content": content[:100]}
            )
