# AI-Toolbox 架构设计

## 设计哲学

> **能力解耦，灵活组合**

AI-Toolbox 的核心设计理念是将各个能力拆分为独立的模块，通过标准接口实现灵活组合，让用户可以像搭积木一样构建自定义 Agent。

---

## 系统架构

```mermaid
graph TB
    subgraph 使用层[使用层]
        CLI[CLI 命令行]
        API[RESTful API]
        Discord[Discord Bot]
        Python[Python API]
    end

    subgraph 能力层[能力层]
        subgraph Providers[AI Providers]
            Kimi[Kimi]
            OpenRouter[OpenRouter]
        end
        
        subgraph Tools[Tools]
            Calc[Calculator]
            Search[WebSearch]
            Time[Time]
            File[File]
            News[News]
        end
        
        Agent[Agent 编排]
        Vision[Vision 视觉]
    end

    subgraph 基础层[基础层]
        Core[Core]
        Config[Config]
        Logger[Logger]
    end

    CLI --> Agent
    CLI --> Tools
    API --> Agent
    Discord --> Agent
    Discord --> Tools
    Python --> Providers
    Python --> Agent
    Python --> Tools

    Agent --> Providers
    Agent --> Tools
    Tools --> Core
    Providers --> Core
    Vision --> Providers
```

---

## 模块详解

### 1. 基础层 (Core)

```mermaid
graph LR
    Core[Core 模块]
    Config[Config 配置管理]
    Logger[Logger 日志系统]
    
    Core --> Config
    Core --> Logger
```

**职责**: 提供所有模块共享的基础设施

**设计原则**:
- 零依赖（除标准库外）
- 所有模块均可独立导入使用

### 2. 能力层 (Capabilities)

#### 2.1 Providers - AI 模型接入

```mermaid
graph TB
    BaseProvider[BaseProvider 抽象基类]
    
    KimiClient[KimiClient]
    OpenRouterClient[OpenRouterClient]
    
    BaseProvider --> KimiClient
    BaseProvider --> OpenRouterClient
    
    Factory[Factory 工厂]
    Factory --> KimiClient
    Factory --> OpenRouterClient
```

**特点**:
- 统一接口 `create_provider()`
- 自动格式转换（Anthropic/OpenAI）
- 支持文本 + 流式 + 多模态

#### 2.2 Tools - 工具能力

```mermaid
graph TB
    Tool[Tool 基类]
    Registry[ToolRegistry 注册表]
    Executor[ToolExecutor 执行器]
    
    Tool --> Registry
    Registry --> Executor
    
    subgraph BuiltInTools[内置工具]
        Calc[Calculator]
        Search[WebSearch]
        Time[Time]
        File[File]
    end
    
    Tool --> BuiltInTools
```

**特点**:
- 每个 Tool 独立实现
- 通过 Registry 动态注册
- Tool 之间无依赖
- 支持同步和异步

#### 2.3 Agent - 能力编排

```mermaid
graph LR
    User[用户输入]
    Agent[Agent]
    Provider[Provider]
    Tools[Tools]
    Response[响应]
    
    User --> Agent
    Agent --> Provider
    Agent --> Tools
    Provider --> Agent
    Tools --> Agent
    Agent --> Response
```

**工作流程**:
1. 接收用户输入
2. 调用 Provider 获取 AI 响应
3. 检测是否需要工具
4. 如需工具，调用 Executor 执行
5. 将结果返回给 AI
6. 返回最终响应

#### 2.4 Vision - 多模态支持

```mermaid
graph TB
    ImageContent[ImageContent]
    MultimodalMessage[MultimodalMessage]
    
    ImageSource[图像来源]
    File[文件]
    URL[URL]
    Base64[Base64]
    
    ImageSource --> File
    ImageSource --> URL
    ImageSource --> Base64
    
    File --> ImageContent
    URL --> ImageContent
    Base64 --> ImageContent
    
    ImageContent --> MultimodalMessage
```

**支持格式**:
- JPEG, PNG, GIF, WebP
- 文件、URL、Base64

### 3. 使用层 (Interfaces)

```mermaid
graph TB
    subgraph Interfaces[接口层]
        CLI[CLI<br/>ai-toolbox chat]
        API[API<br/>/v1/chat]
        Discord[Discord Bot<br/>/chat]
    end
    
    subgraph CoreLogic[核心逻辑]
        Agent[Agent]
        Tools[Tools]
        Providers[Providers]
    end
    
    CLI --> CoreLogic
    API --> CoreLogic
    Discord --> CoreLogic
```

**特点**:
- 每个接口独立运行
- 可单独部署
- 共享能力层

---

## 数据流

### 工具调用流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Agent as Agent
    participant LLM as AI 模型
    participant Tool as 工具
    
    User->>Agent: 发送消息
    Agent->>LLM: 请求响应
    LLM-->>Agent: 返回工具调用
    Agent->>Tool: 执行工具
    Tool-->>Agent: 返回结果
    Agent->>LLM: 发送结果
    LLM-->>Agent: 返回最终响应
    Agent-->>User: 返回结果
```

### Agent 频道模式

```mermaid
sequenceDiagram
    participant User as 用户
    participant Discord as Discord Bot
    participant Agent as Agent
    participant Tools as 工具集
    
    Note over User,Tools: 在 Agent 频道中
    
    User->>Discord: 直接发送消息
    Discord->>Agent: 检测为 Agent 频道
    Agent->>Agent: 处理消息
    
    alt 需要工具
        Agent->>Tools: 调用工具
        Tools-->>Agent: 返回结果
    end
    
    Agent-->>Discord: 返回响应
    Discord-->>User: 显示结果
```

---

## 模块依赖关系

```mermaid
graph BT
    subgraph 上层[上层模块]
        CLI[CLI]
        API[API]
        Discord[Discord Bot]
    end
    
    subgraph 中层[中层模块]
        Agent[Agent]
        Tools[Tools]
        Providers[Providers]
    end
    
    subgraph 下层[下层模块]
        Core[Core]
    end
    
    CLI --> Agent
    CLI --> Tools
    API --> Agent
    Discord --> Agent
    Discord --> Tools
    
    Agent --> Providers
    Agent --> Tools
    Tools --> Core
    Providers --> Core
```

**依赖规则**:
1. Core 无依赖（最底层）
2. Providers/Tools 仅依赖 Core
3. Agent 依赖 Providers + Tools
4. 使用层依赖所有下层模块

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
# 方式 1: 使用 Tool.from_function
from ai_toolbox.tools import Tool

def my_tool(param: str) -> str:
    return f"Result: {param}"

tool = Tool.from_function(
    my_tool,
    description="我的工具"
)

# 方式 2: 手动创建
from ai_toolbox.tools import Tool, ToolParameter

tool = Tool(
    name="my_tool",
    description="我的工具",
    parameters=[
        ToolParameter("param", "string", "参数")
    ],
    function=my_tool
)
```

### 自定义 Agent

```python
from ai_toolbox.agent import Agent

class CustomAgent(Agent):
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

```mermaid
graph LR
    OpenClaw[OpenClaw]
    AIToolbox[AI-Toolbox]
    
    OpenClaw -->|使用| AIToolbox
    AIToolbox -->|调用| OpenClaw
```

**互补定位**:
- **OpenClaw**: 系统级工具、环境控制、多模态输入
- **AI-Toolbox**: AI 模型统一管理、对外 API、工具编排

**协作模式**:
- OpenClaw 可以作为 AI-Toolbox 的消费者
- AI-Toolbox 可以将 OpenClaw 工具封装为 Tool

---

*最后更新: 2026-03-04*