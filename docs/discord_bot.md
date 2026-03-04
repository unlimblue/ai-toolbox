# Discord Bot 模块

Discord 机器人，提供 AI 对话功能。

## 功能

- `/chat` - 与 AI 对话
- `/models` - 查看可用模型
- `/help` - 显示帮助

## 使用方式

### 1. Import 方式

```python
from ai_toolbox.discord_bot import AIToolboxBot

bot = AIToolboxBot()
await bot.start("YOUR_DISCORD_TOKEN")
```

### 2. 独立运行

```bash
export DISCORD_TOKEN=your_token
python -m ai_toolbox.discord_bot
```

## 命令

| 命令 | 描述 | 示例 |
|------|------|------|
| `/chat <prompt>` | 与 AI 对话 | `/chat 你好` |
| `/chat <prompt> [provider]` | 指定提供商 | `/chat 你好 provider:kimi` |
| `/models` | 查看可用模型 | `/models` |
| `/help` | 显示帮助 | `/help` |

## 配置

环境变量：

```bash
DISCORD_TOKEN=your_discord_bot_token
KIMI_API_KEY=your_kimi_key
OPENROUTER_API_KEY=your_or_key
```

## 依赖关系

- **复用**: `core.config`, `core.logger`, `providers`
- **独立**: Bot 逻辑、命令处理、Discord 特定代码
- **无依赖**: API 模块、CLI 模块