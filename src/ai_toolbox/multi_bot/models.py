"""Data models for Multi-Bot System."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class BotState(Enum):
    """Bot state machine states."""
    IDLE = "idle"
    DISCUSSING = "discussing"
    REPORTING = "reporting"


@dataclass
class UnifiedMessage:
    """Unified message format across all channels and bots."""
    id: str
    author_id: str
    author_name: str
    content: str
    channel_id: str
    timestamp: datetime
    mentions: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if self.mentions is None:
            self.mentions = []


@dataclass
class CrossChannelTask:
    """Cross-channel task for coordination between bots."""
    task_id: str
    source_channel: str
    target_channel: str
    target_bots: list[str]
    instruction: str
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    conclusion: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if self.target_bots is None:
            self.target_bots = []


@dataclass
class BotPersona:
    """Bot persona configuration."""
    name: str
    description: str
    system_prompt: str


@dataclass
class ChannelConfig:
    """Channel configuration."""
    channel_id: str
    name: str
    description: str
    allowed_bots: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.allowed_bots is None:
            self.allowed_bots = []


@dataclass
class BotConfig:
    """Bot configuration."""
    bot_id: str
    name: str
    token_env: str
    model_provider: str
    model_name: str
    api_key_env: str
    channels: list[str] = field(default_factory=list)
    persona: Optional[BotPersona] = None
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = []
