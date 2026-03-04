"""AI 相关命令."""

import discord
from discord import app_commands
from discord.ext import commands

from ai_toolbox.core import get_logger
from ai_toolbox.discord_bot.bot import AIToolboxBot

logger = get_logger(__name__)


class AICommands(commands.Cog):
    """AI 对话命令."""

    def __init__(self, bot: AIToolboxBot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="chat", description="与 AI 对话")
    @app_commands.describe(
        prompt="你想问什么？",
        provider="选择 AI 提供商",
        model="选择模型（可选）",
    )
    @app_commands.choices(provider=[
        app_commands.Choice(name="Kimi", value="kimi"),
        app_commands.Choice(name="OpenRouter", value="openrouter"),
    ])
    async def chat(
        self,
        ctx: commands.Context,
        prompt: str,
        provider: str = "kimi",
        model: str | None = None,
    ) -> None:
        """/chat 命令."""
        await ctx.defer()

        try:
            response = await self.bot.chat(
                prompt=prompt,
                provider=provider,
                model=model,
            )

            # 截断长响应
            if len(response) > 2000:
                response = response[:1997] + "..."

            await ctx.reply(f"**AI ({provider}):**\n{response}")

        except Exception as e:
            logger.error(f"Chat error: {e}")
            await ctx.reply(f"❌ 出错了: {str(e)}")

    @commands.hybrid_command(name="models", description="查看可用模型")
    async def models(self, ctx: commands.Context) -> None:
        """/models 命令."""
        embed = discord.Embed(
            title="🤖 可用 AI 模型",
            description="当前可用的 AI 提供商和模型",
            color=discord.Color.blue(),
        )

        for name, client in self.bot.providers.items():
            model_list = "\n".join(f"• `{m}`" for m in client.list_models())
            embed.add_field(name=name.upper(), value=model_list, inline=False)

        await ctx.reply(embed=embed)


async def setup(bot: AIToolboxBot) -> None:
    await bot.add_cog(AICommands(bot))