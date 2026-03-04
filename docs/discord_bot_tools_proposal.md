# Discord Bot 工具集成方案

## 目标
将 ai-toolbox 的工具调用能力集成到 Discord Bot，支持斜杠命令使用工具。

---

## 方案一：专用 Agent 频道（推荐）

### 设计思路
为 Discord Bot 配置专用频道作为 "Agent 频道"，在该频道中 Bot 自动使用工具回答问题。

### 实现方式

#### 1. 配置系统
```python
# 在 discord_bot/bot.py 中添加
class AIToolboxBot(commands.Bot):
    def __init__(self):
        # ... 现有配置 ...
        self.agent_channels: set[int] = set()  # Agent 模式频道
        self.tools_registry: ToolRegistry = self._init_tools()
    
    def _init_tools(self) -> ToolRegistry:
        """初始化工具."""
        registry = ToolRegistry()
        registry.register(calculator_tool)
        registry.register(get_current_time_tool)
        registry.register(WebSearchTool())
        # ... 其他工具
        return registry
```

#### 2. 管理命令
```python
# 管理员命令
@commands.hybrid_command(name="set_agent_channel")
@app_commands.checks.has_permissions(administrator=True)
async def set_agent_channel(self, ctx: commands.Context):
    """将当前频道设为 Agent 频道."""
    self.agent_channels.add(ctx.channel.id)
    await ctx.reply("✅ 此频道已启用 Agent 模式！")

@commands.hybrid_command(name="unset_agent_channel")
@app_commands.checks.has_permissions(administrator=True)
async def unset_agent_channel(self, ctx: commands.Context):
    """取消 Agent 频道."""
    self.agent_channels.discard(ctx.channel.id)
    await ctx.reply("❌ 此频道已禁用 Agent 模式")
```

#### 3. 消息处理
```python
@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    """监听消息，在 Agent 频道自动使用工具."""
    if message.author.bot:
        return
    
    # 只在 Agent 频道响应
    if message.channel.id not in self.agent_channels:
        return
    
    # 使用 Agent 处理
    if not message.content.startswith("!"):  # 忽略命令
        async with message.channel.typing():
            agent = Agent(self.providers.get("kimi"), self.tools_registry)
            response = await agent.run(message.content)
            await message.reply(response)
```

### 优点
- 简单直观，用户无需学习新命令
- 自然对话体验
- 可精确控制哪些频道启用工具

### 缺点
- 需要管理员配置
- 可能误触发工具调用

---

## 方案二：斜杠命令工具

### 设计思路
为每个工具创建独立的斜杠命令，用户按需调用。

### 实现方式

#### 1. 工具命令组
```python
# discord_bot/commands/tools_commands.py
class ToolsCommands(commands.Cog):
    """工具命令."""
    
    def __init__(self, bot: AIToolboxBot):
        self.bot = bot
    
    @commands.hybrid_command(name="calc")
    @app_commands.describe(expression="数学表达式，如 2+2")
    async def calc(self, ctx: commands.Context, expression: str):
        """计算器."""
        result = calculator_tool.function(expression)
        await ctx.reply(f"🧮 结果: {result}")
    
    @commands.hybrid_command(name="search")
    @app_commands.describe(query="搜索关键词")
    async def search(self, ctx: commands.Context, query: str):
        """网络搜索."""
        await ctx.defer()
        search_tool = WebSearchTool()
        result = await search_tool.execute(query)
        # 截断长结果
        if len(result) > 2000:
            result = result[:1997] + "..."
        await ctx.reply(result)
    
    @commands.hybrid_command(name="time")
    @app_commands.describe(timezone="时区，如 Asia/Shanghai")
    async def time(self, ctx: commands.Context, timezone: str = "UTC"):
        """获取当前时间."""
        result = get_current_time_tool.function(timezone)
        await ctx.reply(f"🕐 {result}")
```

#### 2. 智能助手命令
```python
    @commands.hybrid_command(name="ask")
    @app_commands.describe(
        question="你的问题",
        use_tools="是否使用工具"
    )
    async def ask(
        self, 
        ctx: commands.Context, 
        question: str,
        use_tools: bool = True
    ):
        """智能问答（可自动使用工具）."""
        await ctx.defer()
        
        if use_tools:
            agent = Agent(
                self.bot.providers.get("kimi"), 
                self.bot.tools_registry,
                max_iterations=3
            )
            response = await agent.run(question)
        else:
            # 直接对话
            client = self.bot.providers.get("kimi")
            response = await client.chat([ChatMessage(role="user", content=question)])
            response = response.content
        
        await ctx.reply(response)
```

### 优点
- 精确控制，按需使用
- 不会误触发
- 适合特定任务

### 缺点
- 用户需要知道有哪些工具
- 命令较多，学习成本高

---

## 方案三：混合模式（最终推荐）

结合方案一和方案二的优势。

### 实现方式

#### 1. 频道分层
| 频道类型 | 行为 |
|----------|------|
| **普通频道** | 只响应斜杠命令 |
| **Agent 频道** | 自动使用工具 + 斜杠命令 |

#### 2. 斜杠命令结构
```
/ask        - 智能问答（自动工具）
/search     - 网络搜索
/calc       - 计算器
/time       - 当前时间
/file       - 读取文件（需权限）
/tools      - 列出可用工具

/admin
  /set_agent_channel    - 设为 Agent 频道
  /unset_agent_channel  - 取消 Agent 频道
```

#### 3. 权限控制
```python
# 工具权限检查
async def check_tool_permission(tool_name: str, user: discord.User) -> bool:
    """检查用户是否有权限使用工具."""
    # 读取文件需要管理员权限
    if tool_name == "read_file":
        # 检查角色或权限
        pass
    return True
```

#### 4. 配置持久化
```python
# 使用 JSON 存储配置
class BotConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.agent_channels: set[int] = self._load()
    
    def _load(self) -> set[int]:
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                data = json.load(f)
                return set(data.get("agent_channels", []))
        return set()
    
    def save(self):
        with open(self.config_path, "w") as f:
            json.dump({"agent_channels": list(self.agent_channels)}, f)
```

---

## 推荐实现顺序

### Phase 1: 基础工具命令（1天）
1. 添加 `/calc`, `/time`, `/search` 命令
2. 简单直接，无需 Agent 循环

### Phase 2: Agent 问答（1天）
1. 添加 `/ask` 命令（自动工具）
2. 可配置是否使用工具

### Phase 3: Agent 频道（1天）
1. 添加 `/admin set_agent_channel`
2. 消息监听自动处理
3. 配置持久化

### Phase 4: 高级功能（可选）
1. 工具权限系统
2. 对话历史记忆
3. 工具结果缓存

---

## 代码示例

### 完整命令实现
```python
# discord_bot/commands/tools.py
from discord.ext import commands
from ai_toolbox.agent import Agent
from ai_toolbox.tools import (
    calculator_tool,
    get_current_time_tool,
    WebSearchTool,
)

class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command()
    async def calc(self, ctx, expression: str):
        """计算器"""
        result = calculator_tool.function(expression)
        await ctx.reply(f"🧮 {expression} = {result}")
    
    @commands.hybrid_command()
    async def search(self, ctx, *, query: str):
        """搜索网络"""
        await ctx.defer()
        tool = WebSearchTool()
        result = await tool.execute(query)
        await ctx.reply(result[:2000])  # Discord 限制
    
    @commands.hybrid_command()
    async def ask(self, ctx, *, question: str):
        """智能问答"""
        await ctx.defer()
        
        # 创建临时 Agent
        provider = self.bot.providers.get("kimi") or self.bot.providers.get("openrouter")
        if not provider:
            await ctx.reply("❌ 未配置 AI 提供商")
            return
        
        agent = Agent(provider, self.bot.tools_registry, max_iterations=3)
        response = await agent.run(question)
        
        # 分段发送长消息
        if len(response) > 2000:
            for i in range(0, len(response), 2000):
                await ctx.send(response[i:i+2000])
        else:
            await ctx.reply(response)

async def setup(bot):
    await bot.add_cog(Tools(bot))
```

---

## 决策建议

| 场景 | 推荐方案 |
|------|----------|
| 快速启动 | **方案一** (Agent 频道) |
| 精确控制 | **方案二** (斜杠命令) |
| **生产环境** | **方案三** (混合模式) |

**陛下建议采用哪个方案？**