"""通用命令."""

import discord
from discord.ext import commands

from ai_toolbox.discord_bot.bot import AIToolboxBot


class GeneralCommands(commands.Cog):
    """通用命令."""

    def __init__(self, bot: AIToolboxBot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="help", description="显示帮助信息")
    async def help_command(self, ctx: commands.Context) -> None:
        """/help 命令."""
        embed = discord.Embed(
            title="📖 AI-Toolbox 帮助",
            description="可用的命令列表",
            color=discord.Color.green(),
        )

        embed.add_field(
            name="/chat <prompt> [provider]",
            value="与 AI 对话\n例: `/chat 你好 provider:kimi`",
            inline=False,
        )

        embed.add_field(
            name="/models",
            value="查看可用 AI 模型",
            inline=False,
        )

        embed.add_field(
            name="/help",
            value="显示此帮助信息",
            inline=False,
        )

        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """命令错误处理."""
        if isinstance(error, commands.CommandNotFound):
            return

        await ctx.reply(f"❌ 命令执行失败: {str(error)}")


async def setup(bot: AIToolboxBot) -> None:
    await bot.add_cog(GeneralCommands(bot))