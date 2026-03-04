# AI-Toolbox 架构设计文档

## 设计哲学

> **能力解耦，灵活组合**

AI-Toolbox 的核心设计理念是将各个能力拆分为独立的模块，通过标准接口实现灵活组合，让用户可以像搭积木一样构建自定义 Agent。

---

## 架构层次

### 1. 基础层 (Core)

提供所有模块共享的基础设施。

```
core/
├── config.py    # 统一配置管理
├── logger.py    # 日志系统
└── exceptions.py # 异常定义
```

**设计原则**:
- 零依赖（除标准库外）
- 所有模块均可独立导入使用

### 2. 能力层 (Capabilities)

独立的功能模块，每个模块解决一个特定问题。

#### 2.1 Providers - AI 模型接入

```
providers/
├── base.py          # 抽象基类
├── kimi.py          # Kimi 实现
├── openrouter.py    # OpenRouter 实现
└── factory.py       # 工厂函数
```

**独立使用**:
```python
from ai_toolbox.providers import create_provider

client = create_provider("kimi", api_key)
response = await client.chat(messages)
```

**解耦点**:
- 不同提供商完全独立
- 通过统一接口切换
- 新增提供商只需实现基类

#### 2.2 Tools - 工具能力

```
tools/
├── base.py          # Tool 抽象基类
├── registry.py      # 工具注册表
├── executor.py      # 工具执行器
├── search.py        # 网络搜索
├── vision.py        # 图像处理
└── builtin.py       # 内置工具
```

**独立使用**:
```python
from ai_toolbox.tools import WebSearchTool

search = WebSearchTool()
results = await search.search("AI 新闻")
```

**解耦点**:
- 每个 Tool 独立实现
- 通过 Registry 动态注册
- Tool 之间无依赖

#### 2.3 Agent - 能力编排

```
agent/
├── base.py          # Agent 基类
├── react.py         # ReAct Agent
└── planner.py       # 任务规划
```

**组合使用**:
```python
from ai_toolbox.agent import Agent
from ai_toolbox.providers import create_provider
from ai_toolbox.tools import ToolRegistry, WebSearchTool

# 组合各种能力
provider = create_provider("openrouter", api_key)
registry = ToolRegistry()
registry.register(WebSearchTool())

agent = Agent(provider, registry)
```

**解耦点**:
- Agent 不依赖具体 Provider
- Agent 不依赖具体 Tool
- 通过接口组合

### 3. 使用层 (Interfaces)

将能力层封装为不同的使用方式。

```
cli/          # 命令行接口
api/          # RESTful API
discord_bot/  # Discord Bot
```

**特点**:
- 每个接口独立运行
- 可单独部署
- 共享能力层

---

## 模块依赖关系

```
                    ┌─────────────┐
                    │   使用层     │
                    │  CLI/API/   │
                    │ Discord Bot │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐       ┌─────────┐       ┌─────────┐
   │Providers│       │  Tools  │       │  Agent  │
   └────┬────┘       └────┬────┘       └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────┴──────┐
                    │    Core     │
                    │ Config/Log  │
                    └─────────────┘
```

**依赖规则**:
1. Core 无依赖（最底层）
2. Providers/Tools 仅依赖 Core
3. Agent 依赖 Providers + Tools
4. 使用层依赖所有下层模块

---

## 组合示例

### 示例 1: 简单问答 Agent

```python
from ai_toolbox.providers import create_provider
from ai_toolbox.agent import Agent

# 仅使用 Provider
provider = create_provider("kimi", api_key)
agent = Agent(provider)

response = await agent.run("解释量子计算")
```

### 示例 2: 搜索增强 Agent

```python
from ai_toolbox.providers import create_provider
from ai_toolbox.tools import ToolRegistry, WebSearchTool
from ai_toolbox.agent import Agent

# Provider + Search
provider = create_provider("openrouter", api_key)
registry = ToolRegistry()
registry.register(WebSearchTool())

agent = Agent(provider, registry)
response = await agent.run("最新 AI 突破")  # AI 自主搜索
```

### 示例 3: 多模态 Agent

```python
from ai_toolbox.providers import create_provider
from ai_toolbox.tools import (
    ToolRegistry, 
    WebSearchTool, 
    VisionTool,
    CalculatorTool
)
from ai_toolbox.agent import Agent

# 组合所有能力
provider = create_provider("openrouter", api_key)
registry = ToolRegistry()
registry.register(WebSearchTool())
registry.register(VisionTool())
registry.register(CalculatorTool())

agent = Agent(provider, registry)

# AI 可以:
# 1. 分析图片
# 2. 搜索信息
# 3. 计算数据
response = await agent.run("分析这张图表并搜索相关数据")
```

### 示例 4: 自定义 Tool

```python
from ai_toolbox.tools import tool, ToolRegistry

@tool(
    name="my_database",
    description="查询数据库",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        }
    }
)
async def query_database(query: str) -> str:
    # 自定义实现
    return f"查询结果: {query}"

# 注册到 Agent
registry = ToolRegistry()
registry.register(query_database)
```

---

## 扩展指南

### 添加新 Provider

```python
# src/ai_toolbox/providers/new_provider.py
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

# 注册到 factory.py
PROVIDERS["new"] = NewProvider
```

### 添加新 Tool

```python
# src/ai_toolbox/tools/my_tool.py
from .base import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "我的工具"
    parameters = {...}
    
    async def execute(self, **kwargs) -> str:
        # 实现
        return "结果"

# 使用
tool = MyTool()
registry.register(tool)
```

### 自定义 Agent

```python
# src/ai_toolbox/agent/custom.py
from .base import BaseAgent

class CustomAgent(BaseAgent):
    async def run(self, prompt: str) -> str:
        # 自定义逻辑
        # 可以使用 self.provider 和 self.tools
        pass
```

---

## 设计原则检查清单

实现新功能时，检查是否满足：

- [ ] **单一职责**: 每个模块只做一件事
- [ ] **接口隔离**: 通过抽象基类定义接口
- [ ] **依赖倒置**: 高层模块不依赖低层实现
- [ ] **可测试性**: 可以独立单元测试
- [ ] **可组合性**: 可以与其他模块自由组合
- [ ] **三种能力**: 支持 import / CLI / API

---

## 与 OpenClaw 的协作

### OpenClaw 作为能力消费者

```python
# OpenClaw 可以使用 ai-toolbox 的能力
from ai_toolbox.providers import create_provider
from ai_toolbox.tools import WebSearchTool

# 在 OpenClaw 中调用
client = create_provider("kimi", api_key)
response = await client.chat(messages)
```

### ai-toolbox 消费 OpenClaw 工具

```python
# ai-toolbox 可以将 OpenClaw 工具封装为 Tool
@tool(name="web_search", ...)
async def web_search(query: str) -> str:
    # 调用 OpenClaw 的 web_search
    result = await openclaw.web_search(query)
    return result
```

### 理想协作模式

```
┌─────────────────────────────────────┐
│            OpenClaw                  │
│  系统级工具、环境控制、多模态输入      │
└──────────────┬──────────────────────┘
               │
               │ 调用
               ▼
┌─────────────────────────────────────┐
│           ai-toolbox                 │
│  AI 模型管理、工具编排、Agent 构建    │
│  对外 API、Discord Bot              │
└─────────────────────────────────────┘
```