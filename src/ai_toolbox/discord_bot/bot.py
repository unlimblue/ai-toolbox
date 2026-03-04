"""Discord Bot 主类 - 简化版.

仅保留基础聊天功能。
"""

import asyncio
from typing import Any

import discord
from discord.ext import commands

from ai_toolbox.core import get_logger, settings
from ai_toolbox.providers import create_provider, ChatMessage

logger = get_logger(__name__)


class AIToolboxBot(commands.Bot):
    """AI-Toolbox Discord Bot - 简化版.

    仅提供基础 AI 对话功能。

    Usage:
        python -m ai_toolbox.discord_bot
    """

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

        self.providers: dict[str, Any] = {}
        self.default_provider = "kimi"

    async def setup_hook(self) -> None:
        """Bot 启动前的设置."""
        logger.info("Setting up Discord Bot...")

        # 初始化 AI 提供商
        await self._init_providers()

        # 加载命令
        await self.load_extension("ai_toolbox.discord_bot.commands.ai_commands")
        await self.load_extension("ai_toolbox.discord_bot.commands.general_commands")

    async def _init_providers(self) -> None:
        """初始化 AI 提供商客户端."""
        if settings.kimi_api_key:
            self.providers["kimi"] = create_provider("kimi", settings.kimi_api_key)
            logger.info("Kimi provider initialized")

        if settings.openrouter_api_key:
            self.providers["openrouter"] = create_provider(
                "openrouter", settings.openrouter_api_key
            )
            logger.info("OpenRouter provider initialized")

        if not self.providers:
            logger.warning("No AI providers configured!")

    async def on_ready(self) -> None:
        """Bot 就绪事件."""
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        
        # 同步斜杠命令
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="/help"
            )
        )

    async def close(self) -> None:
        """关闭 Bot."""
        logger.info("Shutting down Discord Bot...")

        # 关闭所有提供商客户端
        for provider in self.providers.values():
            await provider.close()

        await super().close()

    async def chat(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """发送聊天请求.

        Args:
            prompt: 用户输入
            provider: 提供商名称 (kimi, openrouter)
            model: 模型名称
            temperature: 温度参数

        Returns:
            AI 响应文本
        """
        provider = provider or self.default_provider

        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not available")

        client = self.providers[provider]
        messages = [ChatMessage(role="user", content=prompt)]

        response = await client.chat(
            messages=messages, model=model, temperature=temperature
        )
        return response.content


async def main() -> None:
    """独立运行入口."""
    if not settings.discord_token:
        logger.error("DISCORD_TOKEN not configured!")
        return

    bot = AIToolboxBot()
    try:
        await bot.start(settings.discord_token)
    except KeyboardInterrupt:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())