"""Message Bus for routing messages between Hub and RoleBots.

Simplified version: only routes messages and maintains ContextGraph.
No hardcoded instruction parsing.
"""

import logging
import uuid
from typing import Dict, Optional, Callable
from datetime import datetime

from .models import UnifiedMessage, CrossChannelTask
from .graph_manager import ContextGraphManager
from .config import DEBUG_AUTHOR_ID, DEBUG_PREFIX

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Simplified message bus.
    
    Responsibilities:
    1. Maintain ContextGraph for conversation history
    2. Route messages to mentioned bots
    
    NO hardcoded parsing, NO task creation.
    """
    
    def __init__(self):
        self.role_bots: Dict[str, object] = {}  # bot_id -> RoleBot
        self.graph_manager = ContextGraphManager()
        self.debug_sender: Optional[Callable] = None
        
        # Channel to bots mapping (for broadcast)
        self.channel_map: Dict[str, list] = {}
    
    def set_debug_sender(self, sender: Callable):
        """Set debug message sender callback."""
        self.debug_sender = sender
    
    async def _send_debug(self, content: str, data: dict = None):
        """Send debug message."""
        if self.debug_sender:
            try:
                await self.debug_sender(content, data)
            except Exception as e:
                logger.error(f"Failed to send debug message: {e}")
    
    def register_bot(self, bot_id: str, bot_instance: object):
        """Register a role bot."""
        self.role_bots[bot_id] = bot_instance
        logger.info(f"Registered bot: {bot_id}")
    
    def register_channel_bots(self, channel_id: str, bot_ids: list):
        """Register which bots can access a channel."""
        self.channel_map[channel_id] = bot_ids
    
    async def publish(self, message: UnifiedMessage):
        """
        Publish message to the bus.
        
        Simplified flow:
        1. Add to ContextGraph
        2. Forward to mentioned bots
        
        No parsing, no task creation.
        """
        # Ignore debug messages
        if str(message.author_id) == DEBUG_AUTHOR_ID:
            return
        if message.content.startswith(DEBUG_PREFIX):
            return
        
        logger.info(f"Publishing message from {message.author_name}")
        await self._send_debug(
            "📤 Publishing message to bus",
            {"author": message.author_name, "mentions": message.mentions}
        )
        
        # 1. Add to ContextGraph (automatic, no parsing)
        graph_id = self._get_graph_id(message.channel_id)
        try:
            self.graph_manager.add_message_to_graph(
                graph_id=graph_id,
                message_id=message.id,
                author_id=message.author_id,
                author_name=message.author_name,
                content=message.content,
                channel_id=message.channel_id,
                timestamp=message.timestamp,
                mention_targets=message.mentions
            )
            await self._send_debug(
                "📝 Added to ContextGraph",
                {"graph_id": graph_id}
            )
        except Exception as e:
            logger.error(f"Error adding to ContextGraph: {e}")
        
        # 2. Forward to mentioned bots (no parsing, direct forward)
        if message.mentions:
            await self._send_debug(
                "📨 Forwarding to mentioned bots",
                {"bots": message.mentions}
            )
            for bot_id in message.mentions:
                if bot_id in self.role_bots:
                    try:
                        await self.role_bots[bot_id].handle_message(
                            message=message,
                            graph_id=graph_id
                        )
                    except Exception as e:
                        logger.error(f"Error forwarding to bot {bot_id}: {e}")
                        await self._send_debug(
                            f"❌ Failed to forward to {bot_id}",
                            {"error": str(e)}
                        )
        else:
            # If no mentions, broadcast to channel bots
            await self._broadcast_to_channel(message)
    
    async def _broadcast_to_channel(self, message: UnifiedMessage):
        """Broadcast message to all bots in channel."""
        channel_bots = self.channel_map.get(message.channel_id, [])
        await self._send_debug(
            "📢 Broadcasting to channel bots",
            {"channel": message.channel_id, "bots": channel_bots}
        )
        
        for bot_id in channel_bots:
            if bot_id in self.role_bots:
                try:
                    graph_id = self._get_graph_id(message.channel_id)
                    await self.role_bots[bot_id].handle_message(
                        message=message,
                        graph_id=graph_id
                    )
                except Exception as e:
                    logger.error(f"Error broadcasting to bot {bot_id}: {e}")
    
    def _get_graph_id(self, channel_id: str) -> str:
        """Get graph ID for a channel."""
        return f"channel_{channel_id}"
    
    def get_context_for_bot(self, graph_id: str, bot_id: str, limit: int = 20):
        """Get context subgraph for a bot."""
        return self.graph_manager.get_context_for_bot(graph_id, bot_id, limit)
