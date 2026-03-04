# API 模块

RESTful API 服务。

## 使用方式

### 启动服务

```bash
# 方式 1: 直接运行
python -m ai_toolbox.api

# 方式 2: 使用 uvicorn
uvicorn ai_toolbox.api:app --host 0.0.0.0 --port 8000
```

## 接口

### POST /v1/chat/completions

聊天补全：

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "kimi",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

响应：

```json
{
  "content": "你好！有什么可以帮助你的吗？",
  "model": "k2p5",
  "usage": {"prompt_tokens": 10, "completion_tokens": 20}
}
```

### GET /v1/models

列出模型：

```bash
curl http://localhost:8000/v1/models?provider=kimi
```

### GET /health

健康检查：

```bash
curl http://localhost:8000/health
```

## 配置

```bash
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your_secret_key  # 可选，用于保护 API
```