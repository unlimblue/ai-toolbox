"""Advanced context filtering and relevance detection for RoleBot."""

from typing import List, Optional
from datetime import datetime, timedelta

from .models import UnifiedMessage, BotState
from .config import DEBUG_AUTHOR_ID, DEBUG_PREFIX


class ContextFilter:
    """
    Advanced context filtering for bot conversations.
    
    Filters messages to provide only relevant context to the bot,
    keeping context window small and focused.
    """
    
    def __init__(self, bot_id: str, max_context: int = 15):
        self.bot_id = bot_id
        self.max_context = max_context
        self.context: List[UnifiedMessage] = []
        # Extended timeout for conversation continuity
        self.conversation_timeout = timedelta(minutes=10)
        self.active_conversation = False
        self.last_mention_time: Optional[datetime] = None
    
    def add_message(self, message: UnifiedMessage) -> bool:
        """
        Add message to context if relevant.
        
        Returns:
            True if message was added, False otherwise
        """
        # Update conversation state
        self._update_conversation_state(message)
        
        if self._is_relevant(message):
            self.context.append(message)
            
            # Trim to max size
            if len(self.context) > self.max_context:
                self.context = self.context[-self.max_context:]
            
            return True
        return False
    
    def _update_conversation_state(self, message: UnifiedMessage):
        """Track conversation state based on mentions."""
        # If bot is mentioned, mark conversation as active
        if self.bot_id in message.mentions:
            self.active_conversation = True
            self.last_mention_time = message.timestamp
    
    def _is_relevant(self, message: UnifiedMessage) -> bool:
        """
        Determine if message is relevant to this bot.
        
        Relevance criteria:
        1. Bot is directly mentioned
        2. Message is from the bot itself
        3. Message is in the same discussion thread
        4. Message is recent and related to current topic
        5. During active conversation, related messages are relevant
        """
        # Ignore debug messages (identified by author_id or content prefix)
        if message.author_id == DEBUG_AUTHOR_ID:
            return False
        
        if message.content.startswith(DEBUG_PREFIX):
            return False
        
        # Direct mention - always relevant
        if self.bot_id in message.mentions:
            return True
        
        # Own message - always relevant
        if message.author_id == self.bot_id:
            return True
        
        # During active conversation, messages from partners are relevant
        if self.active_conversation and self._is_conversation_partner(message):
            return True
        
        # Recent context continuation (extended to 10 minutes during active conversation)
        if self.context:
            last_msg = self.context[-1]
            time_diff = message.timestamp - last_msg.timestamp
            timeout = self.conversation_timeout if self.active_conversation else timedelta(minutes=5)
            
            if time_diff < timeout:
                # Check if it's a reply or continuation
                if self._is_conversation_continuation(message, last_msg):
                    return True
        
        return False
    
    def _is_conversation_partner(self, message: UnifiedMessage) -> bool:
        """Check if message is from a known conversation partner."""
        # If we have context, check if this author has been part of the conversation
        if not self.context:
            return False
        
        # Get recent authors in conversation
        recent_authors = set()
        for msg in self.context[-5:]:  # Check last 5 messages
            recent_authors.add(msg.author_id)
            # Also add anyone they mentioned
            for mention in msg.mentions:
                if mention != self.bot_id:
                    recent_authors.add(mention)
        
        return message.author_id in recent_authors
    
    def _is_conversation_continuation(
        self,
        current: UnifiedMessage,
        previous: UnifiedMessage
    ) -> bool:
        """
        Check if current message is a continuation of previous conversation.
        """
        # Same channel
        if current.channel_id != previous.channel_id:
            return False
        
        # Same author responding
        if current.author_id == previous.author_id:
            return True
        
        # During active conversation, any message in same channel is continuation
        if self.active_conversation:
            return True
        
        return True
    
    def check_conversation_timeout(self) -> bool:
        """
        Check if conversation has timed out.
        
        Returns:
            True if conversation is still active, False if timed out
        """
        if not self.active_conversation:
            return False
        
        if self.last_mention_time is None:
            return False
        
        # Check if 10 minutes have passed since last mention
        if datetime.now() - self.last_mention_time > self.conversation_timeout:
            self.active_conversation = False
            return False
        
        return True
    
    def get_context_for_prompt(self, limit: int = 10) -> str:
        """
        Get formatted context for AI prompt.
        
        Returns:
            Formatted string of recent relevant messages
        """
        messages = self.context[-limit:]
        return "\n".join([
            f"{m.author_name}: {m.content}"
            for m in messages
        ])
    
    def get_recent_mentions(self, limit: int = 5) -> List[UnifiedMessage]:
        """Get recent messages where bot was mentioned."""
        return [
            m for m in self.context
            if self.bot_id in m.mentions
        ][-limit:]
    
    def clear(self):
        """Clear all context."""
        self.context = []
        self.active_conversation = False
        self.last_mention_time = None
    
    def get_stats(self) -> dict:
        """Get context statistics."""
        return {
            "total_messages": len(self.context),
            "mentions": len([m for m in self.context if self.bot_id in m.mentions]),
            "own_messages": len([m for m in self.context if m.author_id == self.bot_id]),
            "channels": len(set(m.channel_id for m in self.context)),
            "active_conversation": self.active_conversation
        }


class RelevanceScorer:
    """
    Scores message relevance for more sophisticated filtering.
    """
    
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
    
    def score(self, message: UnifiedMessage, current_context: List[UnifiedMessage]) -> float:
        """
        Calculate relevance score for a message (0.0 - 1.0).
        
        Higher score = more relevant
        """
        score = 0.0
        
        # Direct mention (highest relevance)
        if self.bot_id in message.mentions:
            score += 1.0
        
        # Own message
        if message.author_id == self.bot_id:
            score += 0.9
        
        # Recent message bonus
        if current_context:
            time_diff = message.timestamp - current_context[-1].timestamp
            if time_diff < timedelta(minutes=2):
                score += 0.3
            elif time_diff < timedelta(minutes=5):
                score += 0.1
        
        # Keyword relevance (simple implementation)
        relevant_keywords = ["结论", "商议", "决策", "方案"]
        for keyword in relevant_keywords:
            if keyword in message.content:
                score += 0.1
        
        return min(score, 1.0)
    
    def should_include(self, message: UnifiedMessage, threshold: float = 0.5) -> bool:
        """Determine if message should be included based on threshold."""
        score = self.score(message, [])
        return score >= threshold
