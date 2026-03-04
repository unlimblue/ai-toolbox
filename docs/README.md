# AI-Toolbox 使用文档

## 目录

- [Providers 模块](providers.md) - AI 模型统一接口
- [CLI 模块](cli.md) - 命令行工具
- [API 模块](api.md) - RESTful API 服务
- [Discord Bot](discord_bot.md) - Discord 机器人

## 快速开始

### 安装

```bash
pip install -e ".[dev]"          # 开发版
pip install -e ".[dev,discord]"  # 包含 Discord Bot
```

### 配置

创建 `.env` 文件：

```bash
KIMI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
DISCORD_TOKEN=your_token  # 如需 Discord Bot
```

### 运行测试

```bash
python scripts/test_all.py
```

## 三种使用方式

| 方式 | 入口 | 说明 |
|------|------|------|
| **Import** | `from ai_toolbox import ...` | Python 模块 |
| **CLI** | `ai-toolbox chat "prompt"` | 命令行 |
| **API** | `python -m ai_toolbox.api` | HTTP 服务 |
| **Discord** | `python -m ai_toolbox.discord_bot` | Discord Bot |