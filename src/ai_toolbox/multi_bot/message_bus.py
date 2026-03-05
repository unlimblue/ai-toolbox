"""Message Bus - Routes messages between bots and manages context."""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Callable

from .models import UnifiedMessage, CrossChannelTask, BotState
from .config import DYNASTY_CONFIG

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Message Bus for routing messages between bots.
    
    Features:
    - Message distribution to relevant bots
    - Cross-channel task coordination
    - Message history tracking
    """
    
    def __init__(self, config=None):
        """
        Initialize Message Bus.
        
        Args:
            config: Optional DynastyConfig instance
        """
        self.config = config or DYNASTY_CONFIG
        self.role_bots: Dict[str, 'RoleBot'] = {}  # bot_id -> RoleBot
        self.channel_map: Dict[str, List[str]] = {}  # channel_id -> bot_ids
        self.message_history: List[UnifiedMessage] = []
        self.active_tasks: Dict[str, CrossChannelTask] = {}
        self._subscribers: List[Callable] = []
        self.max_history = 1000
        self.debug_sender: Optional[Callable] = None  # Callback to send debug messages
    
    def set_debug_sender(self, sender: Callable):
        """Set debug message sender callback."""
        self.debug_sender = sender
    
    async def _send_debug(self, content: str, data: dict = None):
        """Send debug message if debug sender is available."""
        if self.debug_sender:
            try:
                await self.debug_sender(content, data)
            except Exception as e:
                logger.error(f"Failed to send debug message: {e}")
    
    def register_bot(self, bot: 'RoleBot'):
        """
        Register a bot with the message bus.
        
        Args:
            bot: RoleBot instance to register
        """
        bot_id = bot.config.bot_id
        self.role_bots[bot_id] = bot
        
        # Update channel map
        for channel_name in bot.config.channels:
            channel_config = self.config.channels.get(channel_name)
            if channel_config:
                channel_id = channel_config.channel_id
                if channel_id not in self.channel_map:
                    self.channel_map[channel_id] = []
                if bot_id not in self.channel_map[channel_id]:
                    self.channel_map[channel_id].append(bot_id)
        
        logger.info(f"Registered bot: {bot_id}")
    
    def unregister_bot(self, bot_id: str):
        """Unregister a bot."""
        if bot_id in self.role_bots:
            del self.role_bots[bot_id]
            
            # Remove from channel map
            for channel_id, bot_ids in self.channel_map.items():
                if bot_id in bot_ids:
                    bot_ids.remove(bot_id)
            
            logger.info(f"Unregistered bot: {bot_id}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to all messages."""
        self._subscribers.append(callback)
    
    async def publish(self, message: UnifiedMessage):
        """
        Publish a message to the bus.
        
        Args:
            message: UnifiedMessage to publish
        """
        logger.info(f"📤 Publishing message from {message.author_name} to bus")
        
        # Debug: Log publishing
        await self._send_debug(
            "📤 Publishing Message",
            {
                "id": message.id,
                "author": message.author_name,
                "content": message.content[:100],
                "channel": message.channel_id,
                "mentions": message.mentions
            }
        )
        
        # Store in history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
        
        # Notify subscribers
        for subscriber in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(message)
                else:
                    subscriber(message)
            except Exception as e:
                logger.error(f"Subscriber error: {e}")
        
        # Check for cross-channel task
        task = self._parse_cross_channel_task(message)
        if task:
            self.active_tasks[task.task_id] = task
            logger.info(f"🎯 Created cross-channel task: {task.task_id}")
            
            # Debug: Log task creation
            await self._send_debug(
                "🎯 Cross-Channel Task Created",
                {
                    "task_id": task.task_id,
                    "source": task.source_channel,
                    "target": task.target_channel,
                    "target_bots": task.target_bots,
                    "instruction": task.instruction[:100]
                }
            )
            
            # Notify target bots
            for bot_id in task.target_bots:
                if bot_id in self.role_bots:
                    try:
                        logger.info(f"📋 Notifying bot {bot_id} of task")
                        await self._send_debug(
                            f"📋 Notifying Bot: {bot_id}",
                            {"task_id": task.task_id}
                        )
                        await self.role_bots[bot_id].handle_task(task)
                    except Exception as e:
                        logger.error(f"Error notifying bot {bot_id} of task: {e}")
                        await self._send_debug(
                            f"❌ Failed to notify bot {bot_id}",
                            {"error": str(e)}
                        )
        
        # Distribute to relevant bots
        await self._distribute_message(message)
    
    def _parse_cross_channel_task(self, message: UnifiedMessage) -> Optional[CrossChannelTask]:
        """
        Parse cross-channel task from message.
        
        Detects patterns like:
        - "@丞相 @太尉 去内阁商议"
        - "@丞相 到内阁通知太尉"
        """
        from .config_loader import get_config
        config = get_config()
        
        content = message.content.lower()
        original_content = message.content
        
        # Check for cross-channel keywords
        has_mention = "@" in original_content or "<@" in original_content
        has_action = any(k in content for k in ["去", "到", "在", "通知", "叫", "传"])
        
        # Get channel aliases from config
        channel_aliases = {
            "金銮殿": "jinluan",
            "大殿": "jinluan",
            "朝堂": "jinluan",
            "内阁": "neige",
            "议事厅": "neige",
            "商议处": "neige",
            "兵部": "bingbu",
            "军事部": "bingbu",
            "防务处": "bingbu",
        }
        
        # Find which channel is mentioned
        mentioned_channel = None
        for alias, channel_key in channel_aliases.items():
            if alias in content:
                mentioned_channel = channel_key
                break
        
        if not (has_mention and has_action and mentioned_channel):
            return None
        
        # Resolve channel ID from config
        target_channel_id = config.resolve_channel_id(mentioned_channel)
        
        if not target_channel_id:
            return None
        
        # Don't create task if target is same as source
        if target_channel_id == message.channel_id:
            return None
        
        # Collect all target bots
        target_bots = list(message.mentions) if message.mentions else []
        
        # Also check if message content mentions other bots by name
        # This handles "@丞相 去内阁通知太尉" pattern
        for bot_id, bot_config in config.bots.items():
            if bot_id not in target_bots:
                bot_name = bot_config.get('name', '')
                # Check if bot name appears in message (but not as the sender)
                if bot_name and bot_name in original_content:
                    # Make sure this bot isn't the author
                    author_is_bot = False
                    for uid, bid in config.discord_config.get("user_id_to_bot", {}).items():
                        if bid == bot_id and message.author_id == uid:
                            author_is_bot = True
                            break
                    if not author_is_bot:
                        target_bots.append(bot_id)
        
        if not target_bots:
            return None
        
        return CrossChannelTask(
            task_id=str(uuid.uuid4()),
            source_channel=message.channel_id,
            target_channel=target_channel_id,
            target_bots=target_bots,
            instruction=message.content,
            status="pending"
        )
    
    async def _distribute_message(self, message: UnifiedMessage):
        """Distribute message to relevant bots."""
        # Determine target bots
        if message.mentions:
            # If message has mentions, only deliver to mentioned bots
            target_bots = set(message.mentions)
            await self._send_debug(
                "📨 Distributing to mentioned bots only",
                {"mentions": message.mentions}
            )
        else:
            # If no mentions, deliver to all bots in the channel
            channel_bots = self.channel_map.get(message.channel_id, [])
            target_bots = set(channel_bots)
            await self._send_debug(
                "📨 Distributing to all channel bots (no mentions)",
                {"channel_bots": channel_bots}
            )
        
        # Debug: Log distribution
        await self._send_debug(
            f"📨 Distributing to {len(target_bots)} bots",
            {"bots": list(target_bots)}
        )
        
        for bot_id in target_bots:
            if bot_id not in self.role_bots:
                await self._send_debug(
                    f"⚠️ Bot {bot_id} not registered, skipping",
                    {"registered_bots": list(self.role_bots.keys())}
                )
                continue
            
            if self._should_deliver(bot_id, message):
                try:
                    # Debug: Log delivery
                    await self._send_debug(
                        f"➡️ Delivering to {bot_id}",
                        {"message_id": message.id}
                    )
                    await self.role_bots[bot_id].handle_message(message)
                except Exception as e:
                    logger.error(f"Error delivering message to bot {bot_id}: {e}")
                    await self._send_debug(
                        f"❌ Failed to deliver to {bot_id}",
                        {"error": str(e)}
                    )
            else:
                await self._send_debug(
                    f"⏭️ _should_deliver returned False for {bot_id}"
                )
    
    def _should_deliver(self, bot_id: str, message: UnifiedMessage) -> bool:
        """Determine if message should be delivered to bot."""
        # Always deliver if mentioned
        if bot_id in message.mentions:
            return True
        
        # Deliver if in same channel
        channel_bots = self.channel_map.get(message.channel_id, [])
        if bot_id in channel_bots:
            return True
        
        return False
    
    def get_message_history(self, limit: int = 100) -> List[UnifiedMessage]:
        """Get recent message history."""
        return self.message_history[-limit:]
    
    def get_active_tasks(self) -> Dict[str, CrossChannelTask]:
        """Get all active cross-channel tasks."""
        return self.active_tasks.copy()
    
    def complete_task(self, task_id: str, conclusion: str):
        """Mark a task as completed."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = "completed"
            task.conclusion = conclusion
            logger.info(f"Completed task: {task_id}")
