"""Multi-Bot System for Cyber Dynasty Discord Server."""

from .hub_listener import HubListener
from .message_bus import MessageBus
from .role_bot import RoleBot
from .context_filter import ContextFilter, RelevanceScorer
from .config import (
    DYNASTY_CONFIG,
    build_system_prompt,
    ROLE_CHARACTERISTICS,
    DISCORD_ID_TO_BOT_ID,
    BOT_ID_TO_DISCORD_ID,
)
from .models import (
    UnifiedMessage,
    CrossChannelTask,
    BotState,
    BotPersona,
    ChannelConfig,
    BotConfig,
)

__all__ = [
    "HubListener",
    "MessageBus",
    "RoleBot",
    "ContextFilter",
    "RelevanceScorer",
    "DYNASTY_CONFIG",
    "build_system_prompt",
    "ROLE_CHARACTERISTICS",
    "DISCORD_ID_TO_BOT_ID",
    "BOT_ID_TO_DISCORD_ID",
    "UnifiedMessage",
    "CrossChannelTask",
    "BotState",
    "BotPersona",
    "ChannelConfig",
    "BotConfig",
]