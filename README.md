# AI-Toolbox 🤖

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 统一 AI 模型调用接口 - Kimi / OpenRouter

## 快速开始

```bash
pip install -e .
```

配置 API Keys:
```bash
export KIMI_API_KEY=your_key
export OPENROUTER_API_KEY=your_key
```

---

## 🛠️ 工具列表

| 工具 | 描述 | CLI | API | Python |
|------|------|-----|-----|--------|
| **providers** | AI 模型调用 (Kimi, OpenRouter) | ✅ `chat` | ✅ `/v1/chat` | ✅ `create_provider()` |
| **web_search** | 网络搜索 (DuckDuckGo) | ✅ `search` | ❌ | ✅ `WebSearchTool()` |
| **executor** | 异步任务执行器 | ✅ `executor-info` | ✅ `/v1/executor/info` | ✅ `AsyncExecutor()` |
| **discord_bot** | Discord Bot | - | - | ✅ `bot.run()` |

---

## 使用示例

### 1. Providers - AI 对话

**Python:**
```python
from ai_toolbox import create_provider
from ai_toolbox.providers import ChatMessage

client = create_provider("kimi", api_key="your_key")
messages = [ChatMessage(role="user", content="你好")]
response = await client.chat(messages)
print(response.content)
```

**CLI:**
```bash
ai-toolbox chat -p "你好"
```

**API:**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"provider": "kimi", "messages": [{"role": "user", "content": "你好"}]}'
```

---

### 2. Web Search - 网络搜索

**Python:**
```python
from ai_toolbox.web_search import WebSearchTool

search = WebSearchTool()
results = await search.execute("Python 教程")
```

**CLI:**
```bash
ai-toolbox search -q "Python 教程"
```

---

### 3. Executor - 任务执行器

**Python:**
```python
from ai_toolbox.executor import AsyncExecutor

executor = AsyncExecutor(max_workers=4)
result = await executor.execute(my_async_function, args)
```

**CLI:**
```bash
ai-toolbox executor-info --workers 4
```

---

### 4. Discord Bot

**启动:**
```bash
python -m ai_toolbox.discord_bot
```

**命令:**
- `/chat` - 与 AI 对话
- `/models` - 列出模型

---

## CLI 命令

```bash
# Providers
ai-toolbox chat -p "你好"                    # AI 对话
ai-toolbox models                           # 列出模型

# Web Search
ai-toolbox search -q "Python 教程"          # 网络搜索

# Executor
ai-toolbox executor-info --workers 4        # 执行器信息
```

---

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/v1/models` | GET | 列出模型 |
| `/v1/chat/completions` | POST | AI 对话 |

---

## 模块结构

```
ai-toolbox/
├── providers/    # AI 提供商 (Kimi, OpenRouter)
├── web_search/   # 网络搜索
├── executor/     # 任务执行器
├── cli/          # 命令行
├── api/          # RESTful API
└── discord_bot/  # Discord Bot
```

---

## 测试

```bash
pytest
```

---

## License

MIT