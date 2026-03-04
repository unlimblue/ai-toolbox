"""Multi-Bot System for Cyber Dynasty Discord Server."""

from .hub_listener import HubListener
from .message_bus import MessageBus
from .role_bot import RoleBot
from .context_filter import ContextFilter, RelevanceScorer
from .config import DYNASTY_CONFIG, build_system_prompt, ROLE_CHARACTERISTICS
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
    "UnifiedMessage",
    "CrossChannelTask",
    "BotState",
    "BotPersona",
    "ChannelConfig",
    "BotConfig",
]