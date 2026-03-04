# AI-Toolbox 架构设计

## 设计哲学

> **模块化、可组合、易扩展**

每个功能模块独立，可以单独使用，也可以组合使用。

---

## 系统架构

```
ai-toolbox/
├── providers/     # AI 模型提供商
├── web_search/    # 网络搜索
├── executor/      # 沙盒执行器
├── cli/           # 命令行
├── api/           # RESTful API
└── discord_bot/   # Discord Bot
```

---

## 模块详解

### 1. Providers - AI 模型

统一的 AI 提供商接口。

**支持提供商:**
- **Kimi** - Moonshot Kimi for Coding (k2.5)
- **OpenRouter** - 多模型聚合 (Claude, GPT, Gemini)

**使用:**
```python
from ai_toolbox import create_provider

client = create_provider("kimi", api_key="your_key")
response = await client.chat(messages)
```

---

### 2. Web Search - 网络搜索

基于 DuckDuckGo 的免费搜索。

**使用:**
```python
from ai_toolbox.web_search import WebSearchTool

search = WebSearchTool()
results = await search.execute("Python 教程")
```

---

### 3. Executor - 沙盒执行器

安全执行 shell 命令和脚本。

**特性:**
- 超时控制
- 临时文件管理
- 返回码捕获

**使用:**
```python
from ai_toolbox.executor import SandboxExecutor

executor = SandboxExecutor(timeout=30)
result = await executor.run("ls -la")
result = await executor.run_script("print('hello')", language="python")
```

---

### 4. CLI - 命令行

**命令:**
```bash
# Providers
ai-toolbox chat -p "你好"
ai-toolbox models

# Web Search
ai-toolbox search -q "Python 教程"

# Executor
ai-toolbox exec -c "ls -la"
ai-toolbox script -s "print('hello')" -l python
```

---

### 5. API - RESTful 接口

**端点:**
| 端点 | 描述 |
|------|------|
| GET `/health` | 健康检查 |
| GET `/v1/models` | 列出模型 |
| POST `/v1/chat/completions` | AI 对话 |
| GET `/v1/search` | 网络搜索 |
| POST `/v1/execute` | 沙盒执行 |

---

### 6. Discord Bot

基础聊天 Bot。

**命令:**
- `/chat` - 与 AI 对话
- `/models` - 列出可用模型

---

## 工具支持矩阵

| 工具 | Python | CLI | API |
|------|--------|-----|-----|
| providers | ✅ | ✅ | ✅ |
| web_search | ✅ | ✅ | ✅ |
| executor | ✅ | ✅ | ✅ |
| discord_bot | ✅ | - | - |

---

## 快速开始

```bash
# 安装
pip install -e .

# 运行测试
pytest

# 启动 API
python -m ai_toolbox.api

# 启动 Discord Bot
python -m ai_toolbox.discord_bot
```

---

*最后更新: 2026-03-04*