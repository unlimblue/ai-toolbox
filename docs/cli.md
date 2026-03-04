# CLI 模块

命令行接口模块。

## 概述

CLI 模块提供命令行工具，无需编写代码即可与 AI 模型交互。

## 安装

CLI 随主包安装：

```bash
pip install -e .
```

入口命令：`ai-toolbox`

## 命令参考

### chat

与 AI 进行对话。

```bash
ai-toolbox chat [OPTIONS] --prompt <text>
```

**选项**：

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--prompt` | - | 对话内容 | 必需 |
| `--provider` | `-p` | AI 提供商 | `kimi` |
| `--model` | `-m` | 模型名称 | 提供商默认 |
| `--temperature` | `-t` | 温度参数 (0-2) | `0.7` |
| `--stream` | - | 流式输出 | `False` |

**示例**：

```bash
# 基本用法
ai-toolbox chat --prompt "你好"

# 指定提供商
ai-toolbox chat --prompt "你好" --provider openrouter

# 指定模型
ai-toolbox chat --prompt "你好" --provider openrouter --model "anthropic/claude-3-opus"

# 流式输出
ai-toolbox chat --prompt "讲个长故事" --stream

# 低温度（更确定）
ai-toolbox chat --prompt "计算 2+2" --temperature 0.1
```

### models

列出可用的 AI 模型。

```bash
ai-toolbox models [OPTIONS]
```

**选项**：

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--provider` | `-p` | 指定提供商 | `kimi` |

**示例**：

```bash
# 查看 Kimi 模型
ai-toolbox models

# 查看 OpenRouter 模型
ai-toolbox models --provider openrouter
```

## 环境变量

CLI 自动读取 `.env` 文件中的以下变量：

```bash
KIMI_API_KEY=xxx
OPENROUTER_API_KEY=xxx
```

## 错误处理

```bash
# API Key 未配置
$ ai-toolbox chat --prompt "测试"
错误: 未设置 KIMI_API_KEY

# 未知提供商
$ ai-toolbox chat --prompt "test" --provider unknown
错误: Unknown provider: unknown
```

## 实现细节

- 使用 `click` 库构建 CLI
- 支持异步操作
- 自动处理环境变量

## 代码示例

```python
from ai_toolbox.cli.main import cli
from click.testing import CliRunner

runner = CliRunner()
result = runner.invoke(cli, ['chat', '--prompt', '你好'])
print(result.output)
```