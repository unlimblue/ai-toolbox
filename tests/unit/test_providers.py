"""Providers 完整单元测试 - 使用 Mock."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_toolbox.providers import ChatMessage, ChatResponse, create_provider
from ai_toolbox.providers.base import BaseProvider
from ai_toolbox.providers.kimi import KimiClient
from ai_toolbox.providers.openrouter import OpenRouterClient


@pytest.fixture
def mock_api_key():
    """模拟 API key."""
    return "test-api-key-12345"


class TestChatMessage:
    """测试 ChatMessage 数据类."""

    def test_create(self):
        """测试创建消息."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_system_message(self):
        """测试系统消息."""
        msg = ChatMessage(role="system", content="You are a helpful assistant")
        assert msg.role == "system"

    def test_assistant_message(self):
        """测试助手消息."""
        msg = ChatMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"

    def test_immutable(self):
        """测试不可变性."""
        msg = ChatMessage(role="user", content="Hello")
        with pytest.raises(AttributeError):
            msg.role = "assistant"
        with pytest.raises(AttributeError):
            msg.content = "Modified"


class TestChatResponse:
    """测试 ChatResponse 数据类."""

    def test_create(self):
        """测试创建响应."""
        resp = ChatResponse(content="Hello", model="k2p5")
        assert resp.content == "Hello"
        assert resp.model == "k2p5"
        assert resp.usage is None

    def test_with_usage(self):
        """测试带使用统计的响应."""
        usage = {"prompt_tokens": 10, "completion_tokens": 20}
        resp = ChatResponse(content="Hello", model="k2p5", usage=usage)
        assert resp.usage == usage


class TestFactory:
    """测试工厂函数."""

    def test_create_kimi(self, mock_api_key):
        """测试创建 Kimi 客户端."""
        client = create_provider("kimi", mock_api_key)
        assert isinstance(client, KimiClient)
        assert client.api_key == mock_api_key

    def test_create_openrouter(self, mock_api_key):
        """测试创建 OpenRouter 客户端."""
        client = create_provider("openrouter", mock_api_key)
        assert isinstance(client, OpenRouterClient)
        assert client.api_key == mock_api_key

    def test_create_unknown(self):
        """测试未知提供商."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider("unknown", "key")


class TestKimiClient:
    """KimiClient 单元测试."""

    @pytest.fixture
    def kimi_client(self, mock_api_key):
        """创建 Kimi 客户端."""
        return KimiClient(mock_api_key)

    @pytest.mark.asyncio
    async def test_list_models(self, kimi_client):
        """测试列出模型."""
        models = kimi_client.list_models()
        assert isinstance(models, list)
        assert "k2p5" in models

    @pytest.mark.asyncio
    async def test_chat_success(self, kimi_client, mock_api_key):
        """测试聊天成功."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "content": [{"type": "text", "text": "Hello!"}],
            "model": "kimi-for-coding",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        })

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))

        with patch.object(kimi_client, '_get_session', return_value=mock_session):
            messages = [ChatMessage(role="user", content="Hello")]
            response = await kimi_client.chat(messages)

            assert response.content == "Hello!"
            assert response.model == "kimi-for-coding"
            assert response.usage is not None

    @pytest.mark.asyncio
    async def test_chat_api_error(self, kimi_client):
        """测试 API 错误处理."""
        mock_response = MagicMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={
            "error": {"message": "Invalid Authentication"}
        })

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))

        with patch.object(kimi_client, '_get_session', return_value=mock_session):
            messages = [ChatMessage(role="user", content="Hello")]
            with pytest.raises(RuntimeError, match="Kimi API error"):
                await kimi_client.chat(messages)

    @pytest.mark.asyncio
    async def test_chat_with_system_message(self, kimi_client):
        """测试带系统消息的聊天."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "content": [{"type": "text", "text": "Response"}],
            "model": "k2p5"
        })

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))

        with patch.object(kimi_client, '_get_session', return_value=mock_session):
            messages = [
                ChatMessage(role="system", content="You are helpful"),
                ChatMessage(role="user", content="Hello")
            ]
            response = await kimi_client.chat(messages)
            assert response.content == "Response"


class TestOpenRouterClient:
    """OpenRouterClient 单元测试."""

    @pytest.fixture
    def or_client(self, mock_api_key):
        """创建 OpenRouter 客户端."""
        return OpenRouterClient(mock_api_key)

    def test_list_models(self, or_client):
        """测试列出模型."""
        models = or_client.list_models()
        assert isinstance(models, list)
        assert "anthropic/claude-3.5-sonnet" in models
        assert "openai/gpt-4o" in models

    @pytest.mark.asyncio
    async def test_chat_success(self, or_client):
        """测试聊天成功."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Hello!"}}],
            "model": "anthropic/claude-3.5-sonnet",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        })

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))

        with patch.object(or_client, '_get_session', return_value=mock_session):
            messages = [ChatMessage(role="user", content="Hello")]
            response = await or_client.chat(messages)

            assert response.content == "Hello!"
            assert "claude" in response.model

    @pytest.mark.asyncio
    async def test_chat_api_error(self, or_client):
        """测试 API 错误处理."""
        mock_response = MagicMock()
        mock_response.status = 402
        mock_response.json = AsyncMock(return_value={
            "error": {"message": "Insufficient credits"}
        })

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        ))

        with patch.object(or_client, '_get_session', return_value=mock_session):
            messages = [ChatMessage(role="user", content="Hello")]
            with pytest.raises(RuntimeError, match="OpenRouter API error"):
                await or_client.chat(messages)


class TestBaseProvider:
    """测试抽象基类."""

    def test_base_provider_is_abstract(self):
        """测试基类是抽象的."""
        with pytest.raises(TypeError):
            BaseProvider("key")

    def test_subclass_must_implement(self, mock_api_key):
        """测试子类必须实现抽象方法."""
        class IncompleteProvider(BaseProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider(mock_api_key)