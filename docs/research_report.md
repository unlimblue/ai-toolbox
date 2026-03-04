# ai-toolbox 扩展能力调研报告

## 概述

针对前三个高优先级能力：工具调用、视觉模型、网络搜索，进行详细技术方案调研。

---

## 1. 工具调用 (Function Calling)

### 目标
让 AI 能够自主决定调用外部工具，实现自动化工作流。

### 技术方案

#### 1.1 架构设计

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   用户输入   │────▶│  LLM 处理    │────▶│ 文本响应    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼ (如果需要工具)
                    ┌──────────────┐
                    │ 输出 Tool Call│
                    │ (JSON 格式)  │
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ 执行工具     │
                    │ ToolExecutor │
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ 返回结果     │
                    │ 给 LLM      │
                    └──────────────┘
```

#### 1.2 数据模型

```python
# src/ai_toolbox/tools/base.py
from dataclasses import dataclass
from typing import Callable, Any
import json

@dataclass
class Tool:
    """工具定义."""
    name: str
    description: str
    parameters: dict  # JSON Schema
    function: Callable[..., Any]
    
    def to_openai_format(self) -> dict:
        """转换为 OpenAI 工具格式."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def to_anthropic_format(self) -> dict:
        """转换为 Anthropic 工具格式."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }


@dataclass
class ToolCall:
    """工具调用请求."""
    id: str
    name: str
    arguments: dict


@dataclass
class ToolResult:
    """工具执行结果."""
    tool_call_id: str
    content: str
    is_error: bool = False
```

#### 1.3 Provider 支持情况

| 提供商 | 支持情况 | 格式 |
|--------|----------|------|
| OpenRouter (Claude) | ✅ 完全支持 | Anthropic Tools |
| OpenRouter (GPT) | ✅ 完全支持 | OpenAI Tools |
| Kimi Coding | ⚠️ 需验证 | 可能不支持 |

#### 1.4 实现步骤

**Step 1: 创建工具注册器**
```python
# src/ai_toolbox/tools/registry.py
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)
    
    def list_tools(self) -> list[dict]:
        """返回所有工具的 API 格式."""
        return [t.to_openai_format() for t in self._tools.values()]
```

**Step 2: 扩展 Provider 支持工具调用**
```python
# src/ai_toolbox/providers/base.py (扩展)
class ToolEnabledProvider(BaseProvider):
    async def chat_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[Tool],
        tool_choice: str = "auto",  # "auto", "none", or specific tool
        **kwargs
    ) -> ChatResponse | ToolCall:
        """支持工具调用的聊天."""
        pass
```

**Step 3: 实现工具执行器**
```python
# src/ai_toolbox/tools/executor.py
class ToolExecutor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用."""
        tool = self.registry.get(tool_call.name)
        if not tool:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Tool {tool_call.name} not found",
                is_error=True
            )
        
        try:
            # 调用实际函数
            if asyncio.iscoroutinefunction(tool.function):
                result = await tool.function(**tool_call.arguments)
            else:
                result = tool.function(**tool_call.arguments)
            
            return ToolResult(
                tool_call_id=tool_call.id,
                content=str(result)
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Error: {str(e)}",
                is_error=True
            )
```

**Step 4: 创建 Agent 循环**
```python
# src/ai_toolbox/agent.py
class Agent:
    def __init__(self, provider: ToolEnabledProvider, tools: ToolRegistry):
        self.provider = provider
        self.tools = tools
        self.executor = ToolExecutor(tools)
    
    async def run(self, user_input: str, max_iterations: int = 5) -> str:
        """运行 Agent 循环."""
        messages = [ChatMessage(role="user", content=user_input)]
        
        for _ in range(max_iterations):
            response = await self.provider.chat_with_tools(
                messages,
                tools=self.tools.list_tools()
            )
            
            # 如果返回的是工具调用
            if isinstance(response, ToolCall):
                # 执行工具
                result = await self.executor.execute(response)
                
                # 添加工具调用和结果到消息
                messages.append(ChatMessage(
                    role="assistant",
                    content="",
                    tool_calls=[response]  # 需要扩展 ChatMessage
                ))
                messages.append(ChatMessage(
                    role="tool",
                    content=result.content,
                    tool_call_id=result.tool_call_id
                ))
            else:
                # 返回最终文本响应
                return response.content
        
        return "达到最大迭代次数"
```

#### 1.5 内置工具示例

```python
# src/ai_toolbox/tools/builtin.py

# 1. 计算器
@tool(
    name="calculator",
    description="计算数学表达式",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，如 2+2"}
        },
        "required": ["expression"]
    }
)
def calculator(expression: str) -> str:
    try:
        # 安全计算，限制可用函数
        allowed_names = {"abs": abs, "max": max, "min": min}
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"

# 2. 当前时间
@tool(
    name="get_current_time",
    description="获取当前时间",
    parameters={
        "type": "object",
        "properties": {
            "timezone": {"type": "string", "description": "时区，如 Asia/Shanghai"}
        }
    }
)
def get_current_time(timezone: str = "UTC") -> str:
    from datetime import datetime
    import pytz
    tz = pytz.timezone(timezone)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# 3. 文件读取 (sandboxed)
@tool(
    name="read_file",
    description="读取文件内容",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"}
        },
        "required": ["path"]
    }
)
async def read_file(path: str) -> str:
    # 安全检查：限制在 workspace 内
    from pathlib import Path
    full_path = Path(path).resolve()
    workspace = Path("/root/.openclaw/workspace").resolve()
    
    if not str(full_path).startswith(str(workspace)):
        return "错误: 只能访问 workspace 目录内的文件"
    
    try:
        return full_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"读取错误: {e}"
```

#### 1.6 使用示例

```python
# Python
from ai_toolbox import Agent, create_provider
from ai_toolbox.tools import ToolRegistry, calculator, get_current_time

# 创建工具注册表
registry = ToolRegistry()
registry.register(calculator)
registry.register(get_current_time)

# 创建 Agent
provider = create_provider("openrouter", api_key)
agent = Agent(provider, registry)

# 运行
response = await agent.run("计算 123 * 456，并告诉我现在几点")
```

```bash
# CLI
ai-toolbox agent --prompt "计算 2**10" --tools calculator,get_current_time

# API
POST /v1/agent/run
{
  "prompt": "读取 README.md 并总结",
  "tools": ["read_file"],
  "max_iterations": 3
}
```

#### 1.7 工作量评估
| 模块 | 复杂度 | 预计时间 |
|------|--------|----------|
| Tool 数据模型 | 低 | 2h |
| Provider 工具支持 | 中 | 4h |
| Tool Executor | 低 | 2h |
| Agent 循环 | 中 | 4h |
| 内置工具 | 低 | 3h |
| 测试 | 中 | 4h |
| **总计** | **中** | **~2天** |

---

## 2. 视觉模型 (Vision Models)

### 目标
支持图像输入，实现图像理解、OCR、分析等功能。

### 技术方案

#### 2.1 支持模型

| 模型 | 提供商 | 特点 |
|------|--------|------|
| Claude 3 Sonnet/Opus | OpenRouter | 优秀视觉能力 |
| GPT-4V | OpenRouter | 强大多模态 |
| Gemini Pro Vision | OpenRouter | Google 模型 |

#### 2.2 架构设计

```python
# src/ai_toolbox/providers/vision.py
from dataclasses import dataclass
from typing import Literal
import base64

@dataclass
class ImageContent:
    """图像内容."""
    type: Literal["url", "base64", "path"]
    source: str  # URL, base64 string, or file path
    media_type: str = "image/jpeg"  # image/jpeg, image/png, etc.


class VisionMixin:
    """视觉模型 Mixin."""
    
    def _prepare_image(self, image: ImageContent) -> dict:
        """准备图像数据为 API 格式."""
        if image.type == "url":
            return {
                "type": "image_url",
                "image_url": {"url": image.source}
            }
        elif image.type == "base64":
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image.media_type};base64,{image.source}"
                }
            }
        elif image.type == "path":
            # 读取文件并转为 base64
            with open(image.source, "rb") as f:
                base64_data = base64.b64encode(f.read()).decode()
            media_type = f"image/{image.source.split('.')[-1]}"
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{base64_data}"
                }
            }
```

#### 2.3 Provider 实现

**OpenRouter (OpenAI 格式)**:
```python
async def chat_with_image(
    self,
    image: ImageContent,
    prompt: str,
    model: str = "openai/gpt-4o",
    **kwargs
) -> ChatResponse:
    """带图像的聊天."""
    image_content = self._prepare_image(image)
    
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            image_content
        ]
    }]
    
    # 调用 API
    ...
```

**Anthropic 格式**:
```python
# Claude 使用不同的格式
content = [
    {"type": "text", "text": prompt},
    {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": image.media_type,
            "data": image.source if image.type == "base64" else base64_data
        }
    }
]
```

#### 2.4 CLI/API 设计

```bash
# CLI
ai-toolbox vision --image photo.jpg --prompt "描述这张图片"
ai-toolbox vision --image https://example.com/img.png --prompt "提取文字"

# 批量处理
ai-toolbox vision --image-dir ./photos/ --prompt "分析所有图片"
```

```python
# API
POST /v1/vision/analyze
Content-Type: multipart/form-data

image: [二进制文件]
prompt: "描述这张图片"
model: "anthropic/claude-3-opus"
```

#### 2.5 工作量评估
| 模块 | 复杂度 | 预计时间 |
|------|--------|----------|
| ImageContent 模型 | 低 | 1h |
| Provider Vision 支持 | 中 | 3h |
| CLI 图像处理 | 低 | 2h |
| API 文件上传 | 中 | 3h |
| 测试 | 低 | 2h |
| **总计** | **中** | **~1.5天** |

---

## 3. 网络搜索 (Web Search)

### 目标
集成网络搜索，提供实时信息检索能力。

### 技术方案

#### 3.1 搜索后端选择

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **DuckDuckGo** | 免费、无需API Key | 可能有速率限制 | ⭐⭐⭐⭐⭐ |
| **Brave Search** | 高质量结果 | 需要API Key | ⭐⭐⭐⭐ |
| **SerpAPI** | Google结果 | 付费 | ⭐⭐⭐ |
| **Bing API** | Microsoft | 付费 | ⭐⭐⭐ |

**推荐**: 优先实现 DuckDuckGo (零配置)，可选 Brave (高质量)。

#### 3.2 架构设计

```python
# src/ai_toolbox/tools/search.py
from dataclasses import dataclass
from typing import Literal
import aiohttp

@dataclass
class SearchResult:
    """搜索结果."""
    title: str
    url: str
    snippet: str
    source: str  # 搜索引擎来源


class WebSearchTool:
    """网络搜索工具."""
    
    def __init__(
        self,
        provider: Literal["duckduckgo", "brave"] = "duckduckgo",
        api_key: str | None = None,
        max_results: int = 5
    ):
        self.provider = provider
        self.api_key = api_key
        self.max_results = max_results
    
    async def search(self, query: str) -> list[SearchResult]:
        """执行搜索."""
        if self.provider == "duckduckgo":
            return await self._search_duckduckgo(query)
        elif self.provider == "brave":
            return await self._search_brave(query)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    async def _search_duckduckgo(self, query: str) -> list[SearchResult]:
        """使用 DuckDuckGo 搜索."""
        # 使用 duckduckgo-search 库或自己实现
        from duckduckgo_search import AsyncDDGS
        
        async with AsyncDDGS() as ddgs:
            results = []
            async for r in ddgs.text(query, max_results=self.max_results):
                results.append(SearchResult(
                    title=r["title"],
                    url=r["href"],
                    snippet=r["body"],
                    source="duckduckgo"
                ))
            return results
    
    async def _search_brave(self, query: str) -> list[SearchResult]:
        """使用 Brave Search API."""
        if not self.api_key:
            raise ValueError("Brave Search requires API key")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self.api_key},
                params={"q": query, "count": self.max_results}
            ) as resp:
                data = await resp.json()
                return [
                    SearchResult(
                        title=item["title"],
                        url=item["url"],
                        snippet=item["description"],
                        source="brave"
                    )
                    for item in data.get("web", {}).get("results", [])
                ]
    
    async def search_and_fetch(
        self,
        query: str,
        fetch_full_content: bool = False
    ) -> tuple[list[SearchResult], list[str] | None]:
        """搜索并可选获取全文."""
        results = await self.search(query)
        
        if not fetch_full_content:
            return results, None
        
        # 获取前 3 个结果的网页内容
        contents = []
        for result in results[:3]:
            try:
                content = await self._fetch_page(result.url)
                contents.append(content)
            except Exception:
                continue
        
        return results, contents
    
    async def _fetch_page(self, url: str) -> str:
        """获取网页内容并提取文本."""
        # 使用 readability-lxml 或 trafilatura 提取正文
        import trafilatura
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                html = await resp.text()
                text = trafilatura.extract(html)
                return text or ""
```

#### 3.3 与 LLM 集成

```python
# 方式一：作为工具（推荐，与能力1结合）
@tool(
    name="web_search",
    description="搜索网络获取实时信息",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"}
        },
        "required": ["query"]
    }
)
async def web_search_tool(query: str) -> str:
    search = WebSearchTool()
    results = await search.search(query)
    return format_results_for_llm(results)

# 方式二：直接集成
class SearchEnabledProvider:
    async def chat_with_search(
        self,
        messages,
        search_query: str | None = None,
        **kwargs
    ):
        """如果检测到需要搜索，自动执行."""
        # 实现逻辑
        pass
```

#### 3.4 使用示例

```bash
# CLI - 纯搜索
ai-toolbox search "最新 AI 新闻" --provider duckduckgo

# CLI - 搜索并总结
ai-toolbox chat --prompt "总结最新 AI 发展" --with-search

# API
POST /v1/search
{
  "query": "Python 3.12 新特性",
  "provider": "duckduckgo",
  "max_results": 10
}
```

```python
# Python
from ai_toolbox.tools import WebSearchTool

search = WebSearchTool(provider="duckduckgo")
results = await search.search("OpenAI GPT-5")

for r in results:
    print(f"{r.title}: {r.url}")
```

#### 3.5 工作量评估
| 模块 | 复杂度 | 预计时间 |
|------|--------|----------|
| WebSearchTool 基础 | 低 | 2h |
| DuckDuckGo 集成 | 低 | 2h |
| Brave 集成 | 低 | 1h |
| 网页内容提取 | 中 | 3h |
| 与 Tool 系统集成 | 中 | 2h |
| 测试 | 低 | 2h |
| **总计** | **中** | **~1.5天** |

---

## 总结与建议

### 开发优先级

| 优先级 | 能力 | 原因 | 工作量 |
|--------|------|------|--------|
| **P0** | 工具调用 | 基础能力，其他两个可以依赖它 | 2天 |
| **P1** | 网络搜索 | 实用性强，实现简单 | 1.5天 |
| **P2** | 视觉模型 | 独立功能，需求相对较少 | 1.5天 |

### 推荐实现顺序

1. **第一周**: 工具调用系统 + 内置工具（计算器、时间、文件读取）
2. **第二周**: 网络搜索（作为工具集成）
3. **第三周**: 视觉模型支持

### 技术依赖

- **工具调用**: 需要修改 Provider 基类，影响面较大但价值最高
- **网络搜索**: 依赖外部库 (`duckduckgo-search`, `trafilatura`)
- **视觉模型**: 依赖 Provider 支持，主要是 OpenRouter

### 与 OpenClaw 的协作

实现后，ai-toolbox 可以：
- 提供统一的 Tool 接口给 OpenClaw 使用
- OpenClaw 的 `web_search` 可以作为 ai-toolbox 的一个 Tool 实现
- 形成互补：OpenClaw 提供系统级工具，ai-toolbox 提供 AI 模型管理