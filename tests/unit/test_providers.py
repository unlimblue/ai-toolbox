"""Providers 单元测试."""

import pytest
from ai_toolbox.providers import ChatMessage, create_provider
from ai_toolbox.providers.base import BaseProvider, ChatResponse


class TestChatMessage:
    """测试 ChatMessage."""

    def test_create(self):
        """测试创建消息."""
        msg = ChatMessage(role="user", content="你好")
        assert msg.role == "user"
        assert msg.content == "你好"

    def test_immutable(self):
        """测试不可变性."""
        msg = ChatMessage(role="user", content="你好")
        with pytest.raises(AttributeError):
            msg.role = "assistant"


class TestFactory:
    """测试工厂函数."""

    def test_create_kimi(self, mock_api_key):
        """测试创建 Kimi 客户端."""
        client = create_provider("kimi", mock_api_key)
        assert client.api_key == mock_api_key

    def test_create_openrouter(self, mock_api_key):
        """测试创建 OpenRouter 客户端."""
        client = create_provider("openrouter", mock_api_key)
        assert client.api_key == mock_api_key

    def test_create_unknown(self):
        """测试未知提供商."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider("unknown", "key")