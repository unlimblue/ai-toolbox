# Providers 模块

AI 提供商统一接口模块。

## 概述

Providers 模块提供统一的接口来调用不同的 AI 模型，屏蔽底层 API 差异。

## 架构设计

```
providers/
├── base.py       # 抽象基类定义
├── kimi.py       # Kimi (Moonshot) 实现
├── openrouter.py # OpenRouter 实现
└── factory.py    # 工厂函数
```

## 基础使用

### 创建客户端

```python
from ai_toolbox.providers import create_provider

# Kimi
kimi = create_provider("kimi", api_key="your_key")

# OpenRouter
or_client = create_provider("openrouter", api_key="your_key")
```

### 发送消息

```python
from ai_toolbox.providers import ChatMessage

messages = [
    ChatMessage(role="system", content="你是助手"),
    ChatMessage(role="user", content="你好"),
]

response = await client.chat(messages)
print(response.content)
```

### 流式响应

```python
async for chunk in client.stream_chat(messages):
    print(chunk, end="")
```

## API 参考

### ChatMessage

```python
@dataclass(frozen=True)
class ChatMessage:
    role: str      # "system", "user", "assistant"
    content: str
```

### ChatResponse

```python
@dataclass(frozen=True)
class ChatResponse:
    content: str
    model: str
    usage: dict | None
    raw_response: dict | None
```

### BaseProvider

抽象基类，所有提供商必须实现：

| 方法 | 说明 |
|------|------|
| `chat(messages, **kwargs)` | 发送聊天请求 |
| `stream_chat(messages, **kwargs)` | 流式聊天 |
| `list_models()` | 返回可用模型列表 |
| `close()` | 关闭连接 |

## 支持的提供商

### Kimi (Moonshot)

```python
from ai_toolbox.providers.kimi import KimiClient

client = KimiClient(api_key="your_key")

# 可用模型
client.list_models()  # ['k2p5']
```

**特点**：
- 端点：`https://api.kimi.com/coding`
- 格式：Anthropic Messages API
- 模型：`k2p5`

### OpenRouter

```python
from ai_toolbox.providers.openrouter import OpenRouterClient

client = OpenRouterClient(api_key="your_key")

# 可用模型
client.list_models()
# ['anthropic/claude-3.5-sonnet', 'anthropic/claude-3-opus', ...]
```

**特点**：
- 端点：`https://openrouter.ai/api/v1`
- 格式：OpenAI Chat Completions API
- 模型：Claude、GPT、Gemini、Llama 等

## 高级用法

### 自定义参数

```python
response = await client.chat(
    messages=messages,
    model="anthropic/claude-3-opus",  # 指定模型
    temperature=0.5,                   # 温度
    max_tokens=1000,                   # 最大 token
)
```

### 错误处理

```python
from ai_toolbox.providers import create_provider

try:
    client = create_provider("kimi", api_key)
    response = await client.chat(messages)
except ValueError as e:
    # 未知提供商
    print(f"未知提供商: {e}")
except RuntimeError as e:
    # API 错误
    print(f"API 错误: {e}")
```

## 添加新提供商

1. 创建文件 `src/ai_toolbox/providers/new_provider.py`

```python
from .base import BaseProvider, ChatMessage, ChatResponse

class NewProvider(BaseProvider):
    BASE_URL = "https://api.example.com"
    DEFAULT_MODEL = "model-1"

    async def chat(self, messages, **kwargs) -> ChatResponse:
        # 实现 API 调用
        return ChatResponse(
            content="响应",
            model=self.DEFAULT_MODEL,
        )

    async def stream_chat(self, messages, **kwargs):
        # 实现流式响应
        yield "chunk"

    def list_models(self) -> list[str]:
        return ["model-1", "model-2"]

    async def close(self):
        # 清理资源
        pass
```

2. 在 `factory.py` 注册：

```python
from .new_provider import NewProvider

PROVIDERS = {
    "kimi": KimiClient,
    "openrouter": OpenRouterClient,
    "new": NewProvider,  # 添加
}
```

3. 添加单元测试

## 测试

```bash
# Providers 测试
pytest tests/unit/test_providers.py -v

# 覆盖率
pytest tests/unit/test_providers.py --cov=ai_toolbox.providers
```