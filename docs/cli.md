# CLI 模块

命令行接口。

## 安装

```bash
pip install -e .
```

## 命令

### chat

与 AI 对话：

```bash
# 基本用法
ai-toolbox chat --prompt "你好"

# 指定提供商
ai-toolbox chat --prompt "你好" --provider openrouter

# 指定模型
ai-toolbox chat --prompt "你好" --provider openrouter --model "openai/gpt-4o"

# 流式输出
ai-toolbox chat --prompt "讲个故事" --stream
```

### models

列出可用模型：

```bash
ai-toolbox models
ai-toolbox models --provider openrouter
```

### 环境变量

```bash
export KIMI_API_KEY=xxx
export OPENROUTER_API_KEY=xxx
```