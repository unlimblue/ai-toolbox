# AI-Toolbox 🤖

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/unlimblue/ai-toolbox?style=social)](https://github.com/unlimblue/ai-toolbox/stargazers)

<p align="center">
  <img src="https://api.iconify.design/fluent-emoji:toolbox.svg" width="120" alt="AI-Toolbox Logo">
</p>

> **统一 AI 模型调用接口** - Kimi / OpenRouter / 网络搜索 / 沙盒执行

## ✨ 特性

- 🤖 **多模型支持** - Kimi (Moonshot)、OpenRouter (Claude、GPT等)
- 🔍 **网络搜索** - DuckDuckGo 免费搜索
- ⚡ **沙盒执行** - 安全执行 shell 命令和脚本
- 💬 **多接口支持** - Python / CLI / RESTful API / Discord Bot

---

## 🚀 快速开始

```bash
# 安装
pip install -e .

# 配置
export KIMI_API_KEY=your_key
export OPENROUTER_API_KEY=your_key
```

---

## 🛠️ 工具矩阵

| 工具 | 描述 | CLI | API | Python |
|------|------|-----|-----|--------|
| **providers** | AI 模型调用 | ✅ `chat` | ✅ `/v1/chat` | ✅ `create_provider()` |
| **web_search** | 网络搜索 | ✅ `search` | ✅ `/v1/search` | ✅ `WebSearchTool()` |
| **executor** | 沙盒执行器 | ✅ `exec` | ✅ `/v1/execute` | ✅ `SandboxExecutor()` |
| **discord_bot** | Discord Bot | - | - | ✅ `bot.run()` |

---

## 📖 使用示例

### Providers - AI 对话

```python
from ai_toolbox import create_provider
from ai_toolbox.providers import ChatMessage

client = create_provider("kimi", api_key="your_key")
messages = [ChatMessage(role="user", content="你好")]
response = await client.chat(messages)
print(response.content)
```

```bash
# CLI
ai-toolbox chat -p "你好"

# API
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"provider": "kimi", "messages": [{"role": "user", "content": "你好"}]}'
```

### Web Search - 网络搜索

```python
from ai_toolbox.web_search import WebSearchTool

search = WebSearchTool()
results = await search.execute("Python 教程")
```

```bash
# CLI
ai-toolbox search -q "Python 教程"

# API
curl "http://localhost:8000/v1/search?q=Python教程"
```

### Executor - 沙盒执行

```python
from ai_toolbox.executor import SandboxExecutor

executor = SandboxExecutor(timeout=30)
result = await executor.run("ls -la")
print(result.stdout)
```

```bash
# CLI
ai-toolbox exec -c "ls -la"
ai-toolbox script -s "print('hello')" -l python

# API
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la", "timeout": 30}'
```

---

## 🏗️ 架构

```
ai-toolbox/
├── providers/    # AI 提供商 (Kimi, OpenRouter)
├── web_search/   # 网络搜索 (DuckDuckGo)
├── executor/     # 沙盒执行器
├── cli/          # 命令行接口
├── api/          # RESTful API
└── discord_bot/  # Discord Bot
```

---

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/v1/models` | GET | 列出模型 |
| `/v1/chat/completions` | POST | AI 对话 |
| `/v1/search` | GET | 网络搜索 |
| `/v1/execute` | POST | 沙盒执行 |

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=unlimblue/ai-toolbox&type=Date)](https://star-history.com/#unlimblue/ai-toolbox&Date)

---

## 📄 License

[MIT](LICENSE) © unlimblue