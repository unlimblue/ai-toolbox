# Discord Bot 模块

Discord 机器人模块，提供服务器内的 AI 对话功能。

## 概述

Discord Bot 是独立的子模块，提供：
- 🤖 AI 对话功能
- 📋 斜杠命令支持
- 🔌 多提供商切换

## 架构

Discord Bot 是独立模块，仅复用核心组件：

```
discord_bot/
├── __init__.py          # 模块入口
├── bot.py              # Bot 主类
├── commands/           # 命令实现
│   ├── ai_commands.py  # /chat, /models
│   └── general_commands.py  # /help
└── README.md          # 详细文档
```

## 安装

```bash
pip install -e ".[discord_bot]"
```

依赖：`discord.py>=2.4.0`

## 配置

创建 `.env` 文件：

```bash
DISCORD_TOKEN=your_discord_bot_token
KIMI_API_KEY=your_kimi_key
OPENROUTER_API_KEY=your_openrouter_key
```

获取 Discord Token：
1. 访问 https://discord.com/developers/applications
2. 创建 New Application
3. 进入 Bot 标签页，点击 "Add Bot"
4. 复制 Token

## 使用方式

### 方式一：独立运行

```bash
python -m ai_toolbox.discord_bot
```

### 方式二：作为模块

```python
from ai_toolbox.discord_bot import AIToolboxBot

bot = AIToolboxBot()
await bot.start("YOUR_DISCORD_TOKEN")
```

## 命令列表

| 命令 | 描述 | 示例 |
|------|------|------|
| `/chat <prompt>` | 与 AI 对话 | `/chat 你好` |
| `/chat <prompt> [provider]` | 指定提供商 | `/chat 你好 provider:kimi` |
| `/chat <prompt> [model]` | 指定模型 | `/chat 你好 model:claude-3-opus` |
| `/models` | 查看可用模型 | `/models` |
| `/help` | 显示帮助 | `/help` |

## 命令详解

### /chat

与 AI 进行对话。

**参数**：
- `prompt` (必需): 对话内容
- `provider` (可选): 选择提供商 (`kimi`, `openrouter`)
- `model` (可选): 指定模型名称

**示例**：

```
/chat prompt:讲个笑话 provider:kimi
/chat prompt:解释量子力学 model:anthropic/claude-3-opus
```

**响应**：
- 成功: `**AI (kimi):**\n响应内容`
- 失败: `❌ 出错了: 错误信息`
- 长内容自动截断到 2000 字符

### /models

显示当前可用的 AI 提供商和模型。

**响应格式**：
```
🤖 可用 AI 模型
当前可用的 AI 提供商和模型

KIMI
• `k2p5`

OPENROUTER
• `anthropic/claude-3.5-sonnet`
• `anthropic/claude-3-opus`
• ...
```

### /help

显示所有可用命令和说明。

## 权限配置

### Bot 权限

需要的 Discord Intents：
- `message_content`: 读取消息内容
- `messages`: 接收消息事件

### 服务器邀请链接

生成邀请链接（替换 YOUR_CLIENT_ID）：

```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2048&scope=bot%20applications.commands
```

权限值 `2048` = 发送消息 + 使用斜杠命令

## 开发

### 本地测试

```python
import asyncio
from ai_toolbox.discord_bot import AIToolboxBot

async def main():
    bot = AIToolboxBot()
    # 测试 chat 方法
    response = await bot.chat("你好", provider="kimi")
    print(response)

asyncio.run(main())
```

### 添加新命令

1. 在 `commands/` 创建新文件

```python
from discord.ext import commands
from ai_toolbox.discord_bot.bot import AIToolboxBot

class NewCommands(commands.Cog):
    def __init__(self, bot: AIToolboxBot):
        self.bot = bot

    @commands.hybrid_command(name="newcmd")
    async def newcmd(self, ctx):
        await ctx.reply("新命令！")

async def setup(bot: AIToolboxBot):
    await bot.add_cog(NewCommands(bot))
```

2. 在 `bot.py` 加载：

```python
await self.load_extension("ai_toolbox.discord_bot.commands.new_commands")
```

## 测试

```bash
# Discord Bot 测试
pytest tests/unit/discord_bot/ -v
```

## 故障排除

### Bot 不响应

1. 检查 Token 是否正确
2. 确认 Intents 已启用
3. 检查服务器权限

### 命令不出现

1. 确认已同步命令（Bot 启动时自动同步）
2. 重新邀请 Bot（带 `applications.commands` scope）

### API 错误

1. 检查 API Keys 是否配置
2. 确认余额充足

## 与核心模块的关系

**复用的组件**：
- `core.config.settings` - 配置管理
- `core.logger.get_logger` - 日志
- `providers.*` - AI 提供商

**独立的组件**：
- Bot 生命周期管理
- Discord 事件处理
- 命令解析和响应