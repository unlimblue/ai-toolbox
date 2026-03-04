# AI-Toolbox

AI 工具箱 - 统一 AI 模型调用接口，支持 Discord Bot、CLI 和 RESTful API

## 核心原则

1. **精简易读**: 良好抽象，无冗余，一致代码风格
2. **测试驱动**: 所有功能必须有测试，每次开发保证测试通过
3. **三种能力**: 所有工具必须支持 `import`、命令行、RESTful API
4. **文档优先**: 清晰易读且最新的文档

## 使用方式

### 1. 作为 Python 模块

```python
from ai_toolbox.providers import KimiClient

client = KimiClient(api_key="your-key")
response = await client.chat("你好")
```

### 2. 命令行

```bash
ai-toolbox chat --provider kimi --prompt "你好"
```

### 3. RESTful API

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"provider": "kimi", "prompt": "你好"}'
```

## 安装

```bash
pip install -e .
```

## 开发

```bash
pytest  # 运行测试
```

## License

MIT