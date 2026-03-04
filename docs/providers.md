# Providers 模块

统一 AI 模型调用接口。

## 基础使用

```python
from ai_toolbox.providers import create_provider, ChatMessage

# 创建客户端
client = create_provider("kimi", api_key="your_key")

# 发送消息
messages = [ChatMessage(role="user", content="你好")]
response = await client.chat(messages)

print(response.content)
```

## 支持的提供商

| 提供商 | 标识 | 默认模型 |
|--------|------|----------|
| Kimi | `kimi` | `kimi-k2.5` |
| OpenRouter | `openrouter` | `anthropic/claude-3.5-sonnet` |

## 高级用法

```python
# 流式响应
async for chunk in client.stream_chat(messages):
    print(chunk, end="")

# 指定模型
response = await client.chat(
    messages,
    model="anthropic/claude-3-opus",
    temperature=0.5
)

# 查看可用模型
models = client.list_models()
```