# AI-Toolbox 文档

## 文档导航

### 核心文档
- [架构设计](./architecture.md) - 系统架构和使用指南

### 模块文档
- [providers](../src/ai_toolbox/providers/) - AI 模型提供商
- [web_search](../src/ai_toolbox/web_search/) - 网络搜索
- [executor](../src/ai_toolbox/executor/) - 沙盒执行器
- [cli](../src/ai_toolbox/cli/) - 命令行接口
- [api](../src/ai_toolbox/api/) - RESTful API
- [discord_bot](../src/ai_toolbox/discord_bot/) - Discord Bot

## 快速参考

### 安装
```bash
pip install -e .
```

### 配置
```bash
export KIMI_API_KEY=your_key
export OPENROUTER_API_KEY=your_key
```

### 使用示例

**AI 对话:**
```python
from ai_toolbox import create_provider
client = create_provider("kimi", api_key="your_key")
```

**网络搜索:**
```python
from ai_toolbox.web_search import WebSearchTool
search = WebSearchTool()
results = await search.execute("query")
```

**沙盒执行:**
```python
from ai_toolbox.executor import SandboxExecutor
executor = SandboxExecutor()
result = await executor.run("ls -la")
```

---

*详见 [架构设计](./architecture.md)*