# API 模块

RESTful API 服务模块。

## 概述

API 模块提供 HTTP 接口，允许通过 RESTful API 调用 AI 模型。

## 启动服务

### 方式一：模块运行

```bash
python -m ai_toolbox.api
```

默认监听 `0.0.0.0:8000`

### 方式二：Uvicorn

```bash
uvicorn ai_toolbox.api:app --host 0.0.0.0 --port 8000 --reload
```

### 方式三：Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["python", "-m", "ai_toolbox.api"]
```

## API 端点

### POST /v1/chat/completions

聊天补全接口（兼容 OpenAI 格式）。

**请求**：

```json
{
  "provider": "kimi",
  "model": "k2p5",
  "messages": [
    {"role": "system", "content": "你是助手"},
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

**响应**：

```json
{
  "content": "你好！有什么可以帮助你的吗？",
  "model": "kimi-for-coding",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

**参数说明**：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `provider` | string | 是 | 提供商 (kimi, openrouter) |
| `messages` | array | 是 | 消息列表 |
| `model` | string | 否 | 模型名称 |
| `temperature` | float | 否 | 温度 (0-2) |
| `max_tokens` | int | 否 | 最大 token 数 |
| `stream` | bool | 否 | 流式响应 |

### GET /v1/models

列出可用模型。

**请求**：

```bash
GET /v1/models?provider=kimi
```

**响应**：

```json
{
  "provider": "kimi",
  "models": ["k2p5"]
}
```

### GET /health

健康检查。

**响应**：

```json
{
  "status": "ok"
}
```

## 认证

可选的 API Key 认证：

```bash
# 设置环境变量
export API_KEY=your_secret_key

# 请求时添加 Header
curl -H "X-API-Key: your_secret_key" \
  http://localhost:8000/v1/chat/completions
```

## 错误处理

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | API Key 无效 |
| 500 | 服务器内部错误 |

**错误响应**：

```json
{
  "detail": "Error message"
}
```

## 示例

### cURL

```bash
# 基本请求
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "kimi",
    "messages": [{"role": "user", "content": "你好"}]
  }'

# 带认证
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret" \
  -d '{
    "provider": "openrouter",
    "model": "anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json={
        "provider": "kimi",
        "messages": [{"role": "user", "content": "你好"}]
    }
)
print(response.json())
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    provider: 'kimi',
    messages: [{ role: 'user', content: '你好' }]
  })
});
const data = await response.json();
console.log(data.content);
```

## 配置

环境变量：

```bash
API_HOST=0.0.0.0      # 监听地址
API_PORT=8000          # 端口
API_KEY=secret         # 可选，API 认证密钥
```

## 性能

- 客户端连接复用
- 异步处理请求
- 自动清理资源