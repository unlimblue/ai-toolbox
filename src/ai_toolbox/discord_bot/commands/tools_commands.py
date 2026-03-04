"""工具命令 - 斜杠命令方式使用工具."""

import discord
from discord import app_commands
from discord.ext import commands

from ai_toolbox.core import get_logger
from ai_toolbox.discord_bot.bot import AIToolboxBot
from ai_toolbox.agent import Agent
from ai_toolbox.tools import (
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

logger = get_logger(__name__)


class ToolsCommands(commands.Cog):
    """工具命令."""

    def __init__(self, bot: AIToolboxBot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="calc", description="🧮 计算器")
    @app_commands.describe(expression="数学表达式，如 2+2, sqrt(16), sin(pi/2)")
    async def calc(self, ctx: commands.Context, expression: str) -> None:
        """/calc 命令."""
        try:
            result = calculator_tool.function(expression)
            await ctx.reply(f"🧮 `{expression}` = **{result}**")
        except Exception as e:
            await ctx.reply(f"❌ 计算错误: {str(e)}")

    @commands.hybrid_command(name="time", description="🕐 获取当前时间")
    @app_commands.describe(timezone="时区，如 UTC, Asia/Shanghai, America/New_York")
    async def time(self, ctx: commands.Context, timezone: str = "UTC") -> None:
        """/time 命令."""
        try:
            result = get_current_time_tool.function(timezone)
            await ctx.reply(f"🕐 **{timezone}**: {result}")
        except Exception as e:
            await ctx.reply(f"❌ 错误: {str(e)}")

    @commands.hybrid_command(name="random", description="🎲 生成随机数")
    @app_commands.describe(
        min="最小值（默认 0）",
        max="最大值（默认 100）"
    )
    async def random(
        self,
        ctx: commands.Context,
        min: int = 0,
        max: int = 100
    ) -> None:
        """/random 命令."""
        try:
            result = random_number_tool.function(min, max)
            await ctx.reply(f"🎲 [{min}-{max}]: **{result}**")
        except Exception as e:
            await ctx.reply(f"❌ 错误: {str(e)}")

    @commands.hybrid_command(name="choose", description="🎯 随机选择")
    @app_commands.describe(options="逗号分隔的选项，如: 吃饭,睡觉,打代码")
    async def choose(self, ctx: commands.Context, options: str) -> None:
        """/choose 命令."""
        try:
            result = random_choice_tool.function(options)
            await ctx.reply(f"🎯 从 `{options}` 中选择: **{result}**")
        except Exception as e:
            await ctx.reply(f"❌ 错误: {str(e)}")

    @commands.hybrid_command(name="count", description="📝 统计文本字数")
    @app_commands.describe(text="要统计的文本")
    async def count(self, ctx: commands.Context, *, text: str) -> None:
        """/count 命令."""
        try:
            import json
            result = count_words_tool.function(text)
            data = json.loads(result)
            
            embed = discord.Embed(
                title="📝 文本统计",
                color=discord.Color.green()
            )
            embed.add_field(name="中文字符", value=data["chinese_characters"], inline=True)
            embed.add_field(name="英文单词", value=data["english_words"], inline=True)
            embed.add_field(name="数字", value=data["numbers"], inline=True)
            embed.add_field(name="总字符数", value=data["total_characters"], inline=True)
            
            await ctx.reply(embed=embed)
        except Exception as e:
            await ctx.reply(f"❌ 错误: {str(e)}")

    @commands.hybrid_command(name="format_json", description="📋 格式化 JSON")
    @app_commands.describe(data="JSON 字符串")
    async def format_json(self, ctx: commands.Context, *, data: str) -> None:
        """/format_json 命令."""
        try:
            result = format_json_tool.function(data)
            # 使用代码块显示
            await ctx.reply(f"📋 格式化结果:\n```json\n{result[:1900]}\n```")
        except Exception as e:
            await ctx.reply(f"❌ 错误: {str(e)}")

    @commands.hybrid_command(name="search", description="🔍 搜索网络")
    @app_commands.describe(query="搜索关键词")
    async def search(self, ctx: commands.Context, *, query: str) -> None:
        """/search 命令."""
        await ctx.defer()
        
        try:
            tool = WebSearchTool()
            result = await tool.execute(query)
            
            # 截断长结果
            if len(result) > 2000:
                result = result[:1997] + "..."
            
            await ctx.reply(f"🔍 {result}")
        except Exception as e:
            logger.error(f"Search error: {e}")
            await ctx.reply(f"❌ 搜索错误: {str(e)}")

    @commands.hybrid_command(name="news", description="📰 搜索新闻")
    @app_commands.describe(query="新闻关键词")
    async def news(self, ctx: commands.Context, *, query: str) -> None:
        """/news 命令."""
        await ctx.defer()
        
        try:
            tool = WebSearchNewsTool()
            result = await tool.execute(query)
            
            # 截断长结果
            if len(result) > 2000:
                result = result[:1997] + "..."
            
            await ctx.reply(f"📰 {result}")
        except Exception as e:
            logger.error(f"News search error: {e}")
            await ctx.reply(f"❌ 新闻搜索错误: {str(e)}")

    @commands.hybrid_command(name="ask", description="🤖 智能问答（可自动使用工具）")
    @app_commands.describe(
        question="你的问题",
        provider="选择 AI 提供商（默认 Kimi）"
    )
    @app_commands.choices(provider=[
        app_commands.Choice(name="Kimi", value="kimi"),
        app_commands.Choice(name="OpenRouter", value="openrouter"),
    ])
    async def ask(
        self,
        ctx: commands.Context,
        *,
        question: str,
        provider: str = "kimi"
    ) -> None:
        """/ask 命令 - 智能问答，自动使用工具."""
        await ctx.defer()
        
        try:
            # 获取 provider
            client = self.bot.providers.get(provider)
            if not client:
                await ctx.reply(f"❌ 未找到提供商: {provider}")
                return
            
            # 创建 Agent
            agent = Agent(
                client,
                self.bot.tools_registry,
                max_iterations=3
            )
            
            # 运行
            response = await agent.run(question)
            
            # 分段发送长消息
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                await ctx.reply(f"🤖 **AI ({provider})**:\n{chunks[0]}")
                for chunk in chunks[1:]:
                    await ctx.send(chunk)
            else:
                await ctx.reply(f"🤖 **AI ({provider})**:\n{response}")
                
        except Exception as e:
            logger.error(f"Ask error: {e}")
            await ctx.reply(f"❌ 错误: {str(e)}")

    @commands.hybrid_command(name="tools", description="🔧 列出可用工具")
    async def tools(self, ctx: commands.Context) -> None:
        """/tools 命令."""
        embed = discord.Embed(
            title="🔧 可用工具列表",
            description="以下工具可以在 /ask 命令中自动使用",
            color=discord.Color.orange()
        )
        
        tool_descriptions = {
            "calculator": "🧮 计算器 - 数学计算",
            "get_current_time": "🕐 时间 - 获取当前时间",
            "random_number": "🎲 随机数 - 生成随机数",
            "random_choice": "🎯 选择 - 随机选择",
            "count_words": "📝 统计 - 文本字数统计",
            "format_json": "📋 JSON - 格式化 JSON",
            "read_file": "📄 读文件 - 读取文件内容",
            "list_directory": "📁 目录 - 列出目录内容",
            "web_search": "🔍 搜索 - 网络搜索",
            "web_search_news": "📰 新闻 - 新闻搜索",
        }
        
        for name, desc in tool_descriptions.items():
            if self.bot.tools_registry.has(name):
                embed.add_field(name=name, value=desc, inline=True)
        
        embed.set_footer(text="使用 /ask 提问时，AI 会自动选择合适的工具")
        await ctx.reply(embed=embed)


class AdminCommands(commands.Cog):
    """管理员命令."""

    def __init__(self, bot: AIToolboxBot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="set_agent_channel", description="⚙️ 将此频道设为 Agent 频道")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_agent_channel(self, ctx: commands.Context) -> None:
        """设为 Agent 频道."""
        self.bot.agent_channels.add(ctx.channel.id)
        self.bot.save_config()
        await ctx.reply("✅ 此频道已启用 **Agent 模式**！\n现在可以直接对话，AI 会自动使用工具。")

    @commands.hybrid_command(name="unset_agent_channel", description="⚙️ 取消此频道的 Agent 模式")
    @app_commands.checks.has_permissions(administrator=True)
    async def unset_agent_channel(self, ctx: commands.Context) -> None:
        """取消 Agent 频道."""
        self.bot.agent_channels.discard(ctx.channel.id)
        self.bot.save_config()
        await ctx.reply("❌ 此频道已禁用 Agent 模式。")

    @commands.hybrid_command(name="agent_status", description="📊 查看 Agent 频道状态")
    async def agent_status(self, ctx: commands.Context) -> None:
        """查看 Agent 状态."""
        is_agent = ctx.channel.id in self.bot.agent_channels
        
        embed = discord.Embed(
            title="📊 Agent 频道状态",
            color=discord.Color.green() if is_agent else discord.Color.red()
        )
        
        if is_agent:
            embed.add_field(
                name="当前频道",
                value="✅ 已启用 Agent 模式\n可以直接对话，AI 会自动使用工具",
                inline=False
            )
        else:
            embed.add_field(
                name="当前频道",
                value="❌ 未启用 Agent 模式\n请使用 /ask 命令进行智能问答",
                inline=False
            )
        
        # 列出所有 Agent 频道
        if self.bot.agent_channels:
            channels_text = "\n".join([f"• <#{ch_id}>" for ch_id in self.bot.agent_channels])
            embed.add_field(name="所有 Agent 频道", value=channels_text, inline=False)
        
        await ctx.reply(embed=embed)


async def setup(bot: AIToolboxBot) -> None:
    await bot.add_cog(ToolsCommands(bot))
    await bot.add_cog(AdminCommands(bot))