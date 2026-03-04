# AI-Toolbox

AI 工具箱 - 统一 AI 模型调用接口，支持多种使用方式

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 核心原则

1. **精简易读**: 良好抽象，无冗余，一致代码风格
2. **测试驱动**: 所有功能必须有测试，每次开发保证测试通过
3. **三种能力**: 所有工具必须支持 `import`、命令行、RESTful API
4. **文档优先**: 清晰易读且最新的文档

## 功能特性

- 🤖 **多模型支持**: Kimi (Moonshot)、OpenRouter (Claude、GPT 等)
- 💬 **流式响应**: 实时返回 AI 生成内容
- 🔌 **三种调用方式**: Python 模块、CLI、RESTful API
- 🤖 **Discord Bot**: 独立模块，支持斜杠命令

## 快速开始

### 安装

```bash
# 基础安装
pip install -e .

# 包含 Discord Bot
pip install -e ".[discord_bot]"

# 开发环境
pip install -e ".[dev]"
```

### 配置

创建 `.env` 文件：

```bash
# AI Provider API Keys
KIMI_API_KEY=your_kimi_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Discord Bot (可选)
DISCORD_TOKEN=your_discord_bot_token

# API Server (可选)
API_KEY=your_api_key_for_protection
```

### 运行测试

```bash
# 所有测试
pytest

# 带覆盖率
pytest --cov=ai_toolbox

# 集成测试
python scripts/test_all.py
```

## 使用方式

### 1. Python 模块

```python
from ai_toolbox.providers import create_provider, ChatMessage

# 创建客户端
client = create_provider("kimi", api_key="your_key")

# 发送消息
messages = [ChatMessage(role="user", content="你好")]
response = await client.chat(messages)
print(response.content)

# 流式响应
async for chunk in client.stream_chat(messages):
    print(chunk, end="")
```

### 2. 命令行 (CLI)

```bash
# 与 AI 对话
ai-toolbox chat --prompt "你好"

# 指定提供商和模型
ai-toolbox chat --prompt "你好" --provider openrouter --model "anthropic/claude-3.5-sonnet"

# 流式输出
ai-toolbox chat --prompt "讲个故事" --stream

# 查看可用模型
ai-toolbox models
```

### 3. RESTful API

```bash
# 启动服务
python -m ai_toolbox.api

# 或使用 uvicorn
uvicorn ai_toolbox.api:app --host 0.0.0.0 --port 8000
```

发送请求：

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "kimi",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 4. Discord Bot

```bash
# 运行 Bot
python -m ai_toolbox.discord_bot
```

命令：
- `/chat <prompt>` - 与 AI 对话
- `/models` - 查看可用模型
- `/help` - 显示帮助

## 项目结构

```
ai-toolbox/
├── src/ai_toolbox/
│   ├── core/              # 核心配置和工具
│   ├── providers/         # AI 提供商接口
│   │   ├── base.py       # 抽象基类
│   │   ├── kimi.py       # Kimi API
│   │   ├── openrouter.py # OpenRouter API
│   │   └── factory.py    # 工厂函数
│   ├── cli/              # 命令行接口
│   ├── api/              # RESTful API
│   └── discord_bot/      # Discord Bot (独立模块)
├── tests/                # 单元测试和集成测试
├── docs/                 # 文档
└── scripts/              # 脚本工具
```

## 支持的提供商

| 提供商 | 标识 | 默认模型 |
|--------|------|----------|
| Kimi | `kimi` | `k2p5` |
| OpenRouter | `openrouter` | `anthropic/claude-3.5-sonnet` |

## 文档

- [API 文档](docs/api.md) - RESTful API 接口说明
- [CLI 文档](docs/cli.md) - 命令行使用指南
- [Providers 文档](docs/providers.md) - AI 提供商接口
- [Discord Bot 文档](docs/discord_bot.md) - Discord 机器人

## 开发

### 运行测试

```bash
# 单元测试
pytest tests/unit/ -v

# 集成测试
python scripts/test_all.py

# 代码格式
black src/ tests/
ruff check src/ tests/
```

### 添加新提供商

1. 在 `src/ai_toolbox/providers/` 创建新文件
2. 继承 `BaseProvider` 实现必需方法
3. 在 `factory.py` 注册
4. 添加单元测试

示例：

```python
from .base import BaseProvider, ChatMessage, ChatResponse

class NewProvider(BaseProvider):
    async def chat(self, messages, **kwargs) -> ChatResponse:
        # 实现
        pass

    async def stream_chat(self, messages, **kwargs):
        # 实现
        pass

    def list_models(self) -> list[str]:
        return ["model-1", "model-2"]
```

## License

MIT License - 详见 [LICENSE](LICENSE) 文件