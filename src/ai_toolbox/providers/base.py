"""AI 提供商抽象基类."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator


@dataclass(frozen=True)
class ChatMessage:
    """聊天消息."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass(frozen=True)
class ChatResponse:
    """聊天响应."""

    content: str
    model: str
    usage: dict[str, int] | None = None
    raw_response: dict[str, Any] | None = None


class BaseProvider(ABC):
    """AI 提供商抽象基类."""

    def __init__(self, api_key: str, **kwargs: Any):
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ChatResponse:
        """发送聊天请求."""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """流式聊天响应."""
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """返回可用模型列表."""
        pass