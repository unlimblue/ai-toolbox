# AI-Toolbox 文档中心

欢迎来到 AI-Toolbox 文档中心。

## 📚 文档导航

### 入门指南
- [快速开始](../README.md) - 项目介绍和快速上手
- [架构设计](./architecture.md) - 系统架构详解

### 核心模块
- [Providers](./providers.md) - AI 模型提供商接口
- [Tools](./tools.md) - 工具系统详解
- [Agent](./agent.md) - Agent 编排系统
- [Vision](./vision.md) - 视觉/多模态支持

### 使用方式
- [CLI](./cli.md) - 命令行使用指南
- [API](./api.md) - RESTful API 文档
- [Discord Bot](./discord_bot.md) - Discord Bot 使用指南

### 开发文档
- [Contributing](./contributing.md) - 贡献指南
- [Changelog](./changelog.md) - 更新日志

## 🎯 快速导航

| 你想做什么？ | 查看文档 |
|-------------|---------|
| 了解项目架构 | [架构设计](./architecture.md) |
| 使用 AI 模型 | [Providers](./providers.md) |
| 创建自定义工具 | [Tools](./tools.md) |
| 构建 Agent | [Agent](./agent.md) |
| 命令行使用 | [CLI](./cli.md) |
| HTTP API | [API](./api.md) |
| Discord 集成 | [Discord Bot](./discord_bot.md) |

## 💡 示例代码

### 基础示例

```python
from ai_toolbox import create_provider

client = create_provider("kimi", api_key="your_key")
```

### Agent 示例

```python
from ai_toolbox import Agent, create_provider
from ai_toolbox.tools import ToolRegistry, calculator_tool

client = create_provider("openrouter", api_key="your_key")
registry = ToolRegistry()
registry.register(calculator_tool)

agent = Agent(client, registry)
response = await agent.run("计算 123 * 456")
```

### 工具示例

```python
from ai_toolbox.tools import WebSearchTool

search = WebSearchTool()
results = await search.execute("Python 教程")
```

---

*最后更新: 2026-03-04*