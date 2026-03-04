"""Discord Bot 主类."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import discord
from discord.ext import commands

from ai_toolbox.core import get_logger, settings
from ai_toolbox.providers import create_provider, ChatMessage
from ai_toolbox.tools import (
    ToolRegistry,
    calculator_tool,
    get_current_time_tool,
    random_number_tool,
    random_choice_tool,
    count_words_tool,
    format_json_tool,
    read_file_tool,
    list_directory_tool,
    WebSearchTool,
    WebSearchNewsTool,
)
from ai_toolbox.agent import Agent

logger = get_logger(__name__)


class AIToolboxBot(commands.Bot):
    """AI-Toolbox Discord Bot.

    提供 AI 对话功能的 Discord 机器人，支持多种模型提供商和工具调用。

    Usage:
        # 作为模块使用
        from ai_toolbox.discord_bot import AIToolboxBot
        bot = AIToolboxBot()
        await bot.start()

        # 作为服务运行
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
        
        # 工具系统
        self.tools_registry = ToolRegistry()
        self._init_tools()
        
        # Agent 频道配置
        self.config_path = Path("/root/.openclaw/workspace/ai-toolbox/discord_bot_config.json")
        self.agent_channels: set[int] = self._load_config()

    def _init_tools(self) -> None:
        """初始化工具注册表."""
        self.tools_registry.register(calculator_tool)
        self.tools_registry.register(get_current_time_tool)
        self.tools_registry.register(random_number_tool)
        self.tools_registry.register(random_choice_tool)
        self.tools_registry.register(count_words_tool)
        self.tools_registry.register(format_json_tool)
        self.tools_registry.register(read_file_tool)
        self.tools_registry.register(list_directory_tool)
        self.tools_registry.register(WebSearchTool())
        self.tools_registry.register(WebSearchNewsTool())
        
        logger.info(f"Initialized {len(self.tools_registry)} tools")

    def _load_config(self) -> set[int]:
        """加载配置."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    return set(data.get("agent_channels", []))
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        return set()

    def save_config(self) -> None:
        """保存配置."""
        try:
            with open(self.config_path, "w") as f:
                json.dump({
                    "agent_channels": list(self.agent_channels)
                }, f)
            logger.info("Config saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    async def setup_hook(self) -> None:
        """Bot 启动前的设置."""
        logger.info("Setting up Discord Bot...")

        # 初始化 AI 提供商
        await self._init_providers()

        # 加载命令
        await self.load_extension("ai_toolbox.discord_bot.commands.ai_commands")
        await self.load_extension("ai_toolbox.discord_bot.commands.general_commands")
        await self.load_extension("ai_toolbox.discord_bot.commands.tools_commands")

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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """监听消息，处理 Agent 频道."""
        # 忽略 Bot 自己的消息
        if message.author.bot:
            return
        
        # 只在 Agent 频道响应
        if message.channel.id not in self.agent_channels:
            # 非 Agent 频道，继续处理其他命令
            await self.process_commands(message)
            return
        
        # 忽略命令消息（以 ! 开头）
        if message.content.startswith("!"):
            await self.process_commands(message)
            return
        
        # 忽略提及机器人的消息（让其他处理器处理）
        if self.user in message.mentions:
            await self.process_commands(message)
            return
        
        # Agent 模式处理
        await self._handle_agent_message(message)

    async def _handle_agent_message(self, message: discord.Message) -> None:
        """处理 Agent 频道的消息."""
        # 检查是否有可用的提供商
        if not self.providers:
            await message.reply("❌ 未配置 AI 提供商")
            return
        
        # 获取默认提供商
        client = self.providers.get(self.default_provider)
        if not client:
            client = list(self.providers.values())[0]
        
        # 显示正在输入
        async with message.channel.typing():
            try:
                # 创建 Agent
                agent = Agent(
                    client,
                    self.tools_registry,
                    max_iterations=3
                )
                
                # 运行
                response = await agent.run(message.content)
                
                # 分段发送长消息
                if len(response) > 2000:
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    await message.reply(chunks[0])
                    for chunk in chunks[1:]:
                        await message.channel.send(chunk)
                else:
                    await message.reply(response)
                    
            except Exception as e:
                logger.error(f"Agent error: {e}")
                await message.reply(f"❌ 错误: {str(e)}")

    async def close(self) -> None:
        """关闭 Bot."""
        logger.info("Shutting down Discord Bot...")

        # 保存配置
        self.save_config()

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