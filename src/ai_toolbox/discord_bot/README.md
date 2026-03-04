# Discord Bot 文档

Discord Bot 是 AI-Toolbox 的独立模块，提供 Discord 服务器内的 AI 对话功能。

## 架构

```
discord_bot/
├── __init__.py           # 模块入口
├── bot.py               # Bot 主类
├── commands/            # 斜杠命令
│   ├── ai_commands.py   # /chat, /models
│   └── general_commands.py  # /help
└── README.md           # 本文档
```

## 使用方式

### 1. 作为模块使用

```python
from ai_toolbox.discord_bot import AIToolboxBot
import asyncio

async def main():
    bot = AIToolboxBot()
    await bot.start("YOUR_DISCORD_TOKEN")

asyncio.run(main())
```

### 2. 作为独立服务运行

```bash
# 配置环境变量
export DISCORD_TOKEN=your_token_here

# 运行 Bot
python -m ai_toolbox.discord_bot
```

## 命令列表

| 命令 | 描述 | 示例 |
|------|------|------|
| `/chat <prompt>` | 与 AI 对话 | `/chat 你好` |
| `/chat <prompt> provider:kimi` | 指定提供商 | `/chat 你好 provider:kimi` |
| `/models` | 查看可用模型 | `/models` |
| `/help` | 显示帮助 | `/help` |

## 配置

需要配置以下环境变量：

```bash
DISCORD_TOKEN=your_discord_bot_token
KIMI_API_KEY=your_kimi_key          # 可选
OPENROUTER_API_KEY=your_or_key      # 可选
```

## 与核心模块的关系

- **复用**: `core.config`, `core.logger`, `providers`
- **独立**: Bot 逻辑、命令处理、Discord 特定代码
- **无依赖**: API 模块、CLI 模块