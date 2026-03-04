# Providers 模块

AI 模型提供商统一接口。

## 功能

- 支持 Kimi (Moonshot) 和 OpenRouter
- 统一的 `chat()` 和 `stream_chat()` 接口
- 自动处理不同 API 格式差异

## 使用方式

### 1. Import 方式

```python
from ai_toolbox.providers import create_provider, ChatMessage

# 创建客户端
client = create_provider("kimi", api_key="your_key")

# 发送消息
messages = [ChatMessage(role="user", content="你好")]
response = await client.chat(messages)

print(response.content)
```

### 2. CLI 方式

```bash
ai-toolbox chat --provider kimi --prompt "你好"
```

### 3. API 方式

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"provider": "kimi", "messages": [{"role": "user", "content": "你好"}]}'
```

## 支持的提供商

| 提供商 | 标识 | 默认模型 |
|--------|------|----------|
| Kimi | `kimi` | `k2p5` |
| OpenRouter | `openrouter` | `anthropic/claude-3.5-sonnet` |

## 高级用法

### 流式响应

```python
async for chunk in client.stream_chat(messages):
    print(chunk, end="")
```

### 指定模型

```python
response = await client.chat(
    messages,
    model="anthropic/claude-3-opus",
    temperature=0.5,
    max_tokens=1000
)
```

### 查看可用模型

```python
models = client.list_models()
```