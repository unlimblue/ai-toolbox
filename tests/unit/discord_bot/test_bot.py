"""Discord Bot 单元测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_toolbox.discord_bot.bot import AIToolboxBot
from ai_toolbox.providers import ChatMessage


class TestAIToolboxBot:
    """AIToolboxBot 基础测试."""

    def test_bot_initialization(self):
        """测试 Bot 初始化."""
        bot = AIToolboxBot()
        assert bot.command_prefix == "!"
        assert bot.default_provider == "kimi"
        assert isinstance(bot.providers, dict)
        assert len(bot.providers) == 0

    def test_bot_intents(self):
        """测试 Bot 权限配置."""
        bot = AIToolboxBot()
        assert bot.intents.message_content is True

    @pytest.mark.asyncio
    async def test_chat_with_provider(self):
        """测试聊天功能."""
        bot = AIToolboxBot()

        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_provider.chat = AsyncMock(return_value=mock_response)

        bot.providers["kimi"] = mock_provider

        result = await bot.chat("Hello", provider="kimi")
        assert result == "Test response"

    @pytest.mark.asyncio
    async def test_chat_default_provider(self):
        """测试默认提供商."""
        bot = AIToolboxBot()

        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Default response"
        mock_provider.chat = AsyncMock(return_value=mock_response)

        bot.providers["kimi"] = mock_provider

        result = await bot.chat("Test")
        assert result == "Default response"

    @pytest.mark.asyncio
    async def test_chat_invalid_provider(self):
        """测试无效提供商."""
        bot = AIToolboxBot()

        with pytest.raises(ValueError, match="Provider 'invalid' not available"):
            await bot.chat("Test", provider="invalid")

    @pytest.mark.asyncio
    async def test_chat_with_model(self):
        """测试指定模型."""
        bot = AIToolboxBot()

        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Model response"
        mock_provider.chat = AsyncMock(return_value=mock_response)

        bot.providers["openrouter"] = mock_provider

        result = await bot.chat(
            "Test",
            provider="openrouter",
            model="claude-3-opus",
            temperature=0.5
        )

        assert result == "Model response"
        call_kwargs = mock_provider.chat.call_args.kwargs
        assert call_kwargs.get("model") == "claude-3-opus"
        assert call_kwargs.get("temperature") == 0.5

    @pytest.mark.asyncio
    async def test_close_providers(self):
        """测试关闭时清理提供商."""
        bot = AIToolboxBot()

        mock_provider = MagicMock()
        mock_provider.close = AsyncMock()
        bot.providers["kimi"] = mock_provider

        with patch.object(type(bot).__bases__[0], 'close', new_callable=AsyncMock):
            await bot.close()
            mock_provider.close.assert_called_once()


class TestChatMessageFormat:
    """测试聊天消息格式."""

    @pytest.mark.asyncio
    async def test_chat_message_conversion(self):
        """测试消息转换为 ChatMessage."""
        bot = AIToolboxBot()

        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "OK"
        mock_provider.chat = AsyncMock(return_value=mock_response)

        bot.providers["kimi"] = mock_provider

        await bot.chat("User input")

        call_args = mock_provider.chat.call_args
        messages = call_args.kwargs.get("messages") or call_args.args[0]

        assert len(messages) == 1
        assert isinstance(messages[0], ChatMessage)
        assert messages[0].role == "user"
        assert messages[0].content == "User input"


class TestProviderInitialization:
    """测试提供商初始化."""

    @pytest.mark.asyncio
    async def test_init_with_env_vars(self):
        """测试环境变量配置."""
        with patch.dict("os.environ", {
            "KIMI_API_KEY": "kimi_test_key",
            "OPENROUTER_API_KEY": "or_test_key"
        }, clear=False):
            bot = AIToolboxBot()

            with patch("ai_toolbox.discord_bot.bot.create_provider") as mock_create:
                mock_create.return_value = MagicMock()
                await bot._init_providers()

                # 应该创建两个提供商
                assert mock_create.call_count == 2
                assert "kimi" in bot.providers
                assert "openrouter" in bot.providers

    @pytest.mark.asyncio
    async def test_init_no_providers(self):
        """测试无提供商配置."""
        # Mock settings 返回 None
        with patch("ai_toolbox.discord_bot.bot.settings") as mock_settings:
            mock_settings.kimi_api_key = None
            mock_settings.openrouter_api_key = None

            bot = AIToolboxBot()
            await bot._init_providers()
            assert len(bot.providers) == 0