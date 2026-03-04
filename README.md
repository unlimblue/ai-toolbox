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

## 使用

### Python API

```python
from ai_toolbox import create_provider
from ai_toolbox.providers import ChatMessage

client = create_provider("kimi", api_key="your_key")
messages = [ChatMessage(role="user", content="你好")]
response = await client.chat(messages)
print(response.content)
```

### CLI

```bash
# 对话
ai-toolbox chat -p "你好"

# 搜索
ai-toolbox search -q "Python 教程"

# 列出模型
ai-toolbox models
```

### Web Search

```python
from ai_toolbox.web_search import WebSearchTool

search = WebSearchTool()
results = await search.execute("Python 教程")
```

### Executor

```python
from ai_toolbox.executor import AsyncExecutor

executor = AsyncExecutor(max_workers=4)
result = await executor.execute(my_async_function, args)
```

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

## 测试

```bash
pytest
```

## License

MIT