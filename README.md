# AI-Toolbox

AI 工具箱 - 统一 AI 模型调用接口，支持 Discord Bot、CLI 和 RESTful API

## 核心原则

1. **精简易读**: 良好抽象，无冗余，一致代码风格
2. **测试驱动**: 所有功能必须有测试，每次开发保证测试通过
3. **三种能力**: 所有工具必须支持 `import`、命令行、RESTful API
4. **文档优先**: 清晰易读且最新的文档

## 快速开始

### 安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装
pip install -e ".[dev]"
```

### 配置

复制 `.env.example` 为 `.env` 并填入 API Keys：

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Keys
```

### 运行测试

```bash
# 单元测试
pytest tests/ -v

# 集成测试（需要有效 API Keys）
python scripts/test_all.py
```

## 模块文档

| 模块 | 描述 | 使用方式 |
|------|------|----------|
| [providers](docs/providers.md) | AI 模型统一接口 | `import` / CLI / API |
| [cli](docs/cli.md) | 命令行工具 | `ai-toolbox` 命令 |
| [api](docs/api.md) | RESTful API 服务 | HTTP 接口 |
| [discord_bot](docs/discord_bot.md) | Discord 机器人 | 模块 / 独立运行 |

## 项目结构

```
ai-toolbox/
├── src/ai_toolbox/
│   ├── core/           # 配置、日志等核心功能
│   ├── providers/      # AI 提供商接口 (Kimi, OpenRouter)
│   ├── cli/            # 命令行接口
│   ├── api/            # RESTful API
│   └── discord_bot/    # Discord Bot
├── tests/              # 单元测试
├── docs/               # 文档
└── scripts/            # 工具脚本
```

## License

MIT