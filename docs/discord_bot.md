# Discord Bot 模块

Discord 机器人，提供 AI 对话功能。

## 架构

Discord Bot 是独立模块，仅复用核心配置和 providers。

```
discord_bot/
├── bot.py           # Bot 主类
├── commands/        # 斜杠命令
└── README.md        # 详细文档
```

## 使用

### 模块方式

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

## 详细文档

参见 `src/ai_toolbox/discord_bot/README.md`