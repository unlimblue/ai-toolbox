# Discord Bot

Discord 机器人模块，提供 AI 对话功能。

## 使用方式

### 作为模块使用

```python
from ai_toolbox.discord_bot import AIToolboxBot

bot = AIToolboxBot()
await bot.start("YOUR_DISCORD_TOKEN")
```

### 独立运行

```bash
export DISCORD_TOKEN=your_token
python -m ai_toolbox.discord_bot
```

## 命令

| 命令 | 描述 |
|------|------|
| `/chat <prompt>` | 与 AI 对话 |
| `/models` | 查看可用模型 |
| `/help` | 显示帮助 |

## 配置

```bash
DISCORD_TOKEN=your_discord_bot_token
KIMI_API_KEY=your_kimi_key          # 可选
OPENROUTER_API_KEY=your_or_key      # 可选
```

## 依赖关系

- **复用**: `core.config`, `core.logger`, `providers`
- **独立**: Bot 逻辑、命令处理、Discord 特定代码