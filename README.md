<div align="center">

# 🤖 AI-Toolbox

**AI 驱动的多 Bot 协作系统**

[![GitHub Stars](https://img.shields.io/github/stars/unlimblue/ai-toolbox?style=social)](https://github.com/unlimblue/ai-toolbox)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <img src="https://img.shields.io/badge/Discord-Bot-5865F2?logo=discord&logoColor=white" alt="Discord">
  <img src="https://img.shields.io/badge/Kimi-AI-FF6B6B" alt="Kimi AI">
  <img src="https://img.shields.io/badge/Context-Graph-4ECDC4" alt="Context Graph">
</p>

**让 AI Bots 像人类一样自主协作**

[English](README_EN.md) | 简体中文

</div>

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=unlimblue/ai-toolbox&type=Date)](https://star-history.com/#unlimblue/ai-toolbox&Date)

---

## 📖 目录

- [设计理念](#-设计理念)
- [快速开始](#-快速开始)
- [系统架构](#-系统架构)
- [核心功能](#-核心功能)
- [使用示例](#-使用示例)
- [配置指南](#-配置指南)
- [API 文档](#-api文档)
- [其他工具](#-其他工具)
- [贡献指南](#-贡献指南)

---

## 💡 设计理念

### 核心思想：自主决策架构

传统 Bot 系统采用**命令-执行**模式：系统解析指令 → 分配给 Bot → Bot 执行固定动作。这种模式限制了 AI 的灵活性。

**AI-Toolbox** 采用全新的**自主决策架构**：

```
┌─────────────────────────────────────────────────────────────┐
│                     自主决策架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户："@丞相 去内阁通知太尉，然后回金銮殿汇报"                │
│                      ↓                                       │
│  系统：转发消息给丞相（不做任何解析）                          │
│                      ↓                                       │
│  丞相 AI：自主理解指令 → 决策 → 执行                          │
│     ├─ 在内阁 @太尉："太尉大人，陛下召您前往金銮殿"            │
│     └─ 在金銮殿回复："启禀陛下，已通知太尉"                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 设计原则

| 原则 | 说明 |
|------|------|
| **无硬编码** | 不解析指令、不预设流程，完全由 AI 自主决策 |
| **Context Graph** | 自动维护对话上下文，保证多轮对话连贯性 |
| **多动作能力** | 单条指令可触发多个频道的多轮对话 |
| **配置驱动** | 通过 YAML 配置角色、频道、行为，无需修改代码 |

---

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/unlimblue/ai-toolbox.git
cd ai-toolbox
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. 配置环境变量

```bash
# 创建 secrets 文件
mkdir -p ~/.openclaw/secrets
cat > ~/.openclaw/secrets/cyber_dynasty_tokens.env << 'EOF'
# Discord Tokens
HUB_BOT_TOKEN=your_hub_bot_token
CHENGXIANG_BOT_TOKEN=your_chengxiang_bot_token
TAIWEI_BOT_TOKEN=your_taiwei_bot_token

# AI Provider
KIMI_API_KEY=your_kimi_api_key
EOF
```

### 3. 启动服务

```bash
./scripts/multi_bot.sh start
```

### 4. 测试

在 Discord 频道中：

```
@丞相 @太尉 去内阁商议边防方案
```

---

## 🏗️ 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI-Toolbox 架构                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   Discord    │────▶│  HubListener │────▶│ MessageBus   │   │
│  │   Gateway    │     │              │     │              │   │
│  └──────────────┘     └──────────────┘     └──────┬───────┘   │
│                                                    │            │
│                           ┌────────────────────────┘            │
│                           ▼                                     │
│                    ┌──────────────┐                            │
│                    │ContextGraph  │                            │
│                    │Manager       │                            │
│                    └──────┬───────┘                            │
│                           │                                     │
│              ┌────────────┼────────────┐                       │
│              ▼            ▼            ▼                       │
│       ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│       │ 丞相 Bot │ │ 太尉 Bot │ │ 其他 Bot │                  │
│       └──────────┘ └──────────┘ └──────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 职责 | 特点 |
|------|------|------|
| **HubListener** | Discord 消息监听 | 将 Discord 消息转为统一格式 |
| **MessageBus** | 消息路由 | 无解析，直接转发给被 @ 的 Bot |
| **ContextGraphManager** | 上下文管理 | 自动计算可见性，提取相关上下文 |
| **RoleBot** | 自主决策执行 | AI 决定频道、内容、@对象 |

### Context Graph 机制

```
金銮殿图:
  用户: "@丞相 去内阁通知太尉"
       │
       ├── 可见: [丞相] (被@)
       │
       └── 丞相的消息 ──► 内阁图合并

内阁图:
  丞相: "@太尉 请前来"
       │
       ├── 可见: [丞相, 太尉]
       │
       └── 太尉的回复 ──► 可见性传播

可见性传播规则:
1. 被 @ 的 Bot 可见
2. 父消息可见者，子消息也可见
3. 同频道参与者可见
```

---

## ✨ 核心功能

### 1. 自主频道选择

Bot 根据指令自主决定在哪里响应：

| 指令 | 丞相动作 |
|------|---------|
| "@丞相 去内阁通知太尉" | 去内阁 @太尉 |
| "@丞相 来金銮殿汇报" | 在金銮殿回复 |
| "@丞相 通知太尉来金銮殿" | 去内阁 @太尉 → 回金銮殿汇报 |

### 2. 多动作执行

单条指令触发多频道多轮对话：

```
用户: "@丞相 @太尉 去内阁商议后汇报"

丞相:
  [内阁] @太尉 "太尉大人，请商议边防"
  [内阁] 与太尉讨论...
  [金銮殿] "启禀陛下，商议结果：..."
```

### 3. Context Graph 上下文

自动维护跨频道对话历史：

```
太尉在内阁能看到：
- 丞相的召集消息
- 之前的讨论历史
- 完整的对话上下文
```

### 4. 配置驱动角色

通过 YAML 定义新角色，无需改代码：

```yaml
bots:
  my_new_bot:
    name: "新角色"
    persona:
      description: "角色描述"
      custom_instructions: |
        ## 自主决策指南
        ...
```

---

## 📚 使用示例

### 基础对话

```
金銮殿> @丞相 查询今日政务
丞相: 启禀陛下，今日政务如下：...
```

### 跨频道任务

```
金銮殿> @丞相 @太尉 去内阁商议边防方案

丞相: 领旨，即刻前往内阁。
[内阁] 丞相: @太尉 太尉大人，请前来商议。
[内阁] 太尉: 丞相大人，臣在。边防方案...
[内阁] 丞相: 那就按此方案执行。
[金銮殿] 丞相: 启禀陛下，商议完毕，方案：...
```

### 多轮对话

```
金銮殿> @丞相 与太尉讨论后决定

[内阁]
丞相: @太尉 此事如何？
太尉: 臣以为可行，但需注意...
丞相: @太尉 所言极是，还有补充？
太尉: 没有了，请丞相定夺。

[金銮殿]
丞相: 启禀陛下，臣与太尉商议已定...
```

---

## ⚙️ 配置指南

### 配置文件结构

```yaml
config/
├── multi_bot.yaml          # 主配置
└── organizations/          # 多组织配置
    └── corporate.yaml      # 企业版配置示例
```

### 主配置示例

```yaml
organization:
  name: "赛博王朝"
  description: "AI 模拟组织"

discord:
  channels:
    jinluan:
      id: "1478759781425745940"
      name: "金銮殿"
      allowed_bots: ["chengxiang", "taiwei"]

bots:
  chengxiang:
    name: "丞相"
    model_provider: "kimi"
    model_name: "kimi-k2-5"
    persona:
      description: "三公之首，统筹决策"
      custom_instructions: |
        ## 自主决策指南
        你可以自主选择在哪个频道发送消息...
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `HUB_BOT_TOKEN` | Hub Bot Discord Token |
| `CHENGXIANG_BOT_TOKEN` | 丞相 Bot Token |
| `TAIWEI_BOT_TOKEN` | 太尉 Bot Token |
| `KIMI_API_KEY` | Kimi API Key |

---

## 📚 文档导航

| 文档 | 内容 |
|------|------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 详细架构设计 |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | 部署指南 |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | 配置详解 |
| [docs/API.md](docs/API.md) | API 文档 |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | 开发指南 |

---

## 🛠️ 其他工具

AI-Toolbox 还包含以下独立工具：

| 工具 | 说明 | 文档 |
|------|------|------|
| `web_search` | 网页搜索 | [docs/tools/web_search.md](docs/tools/web_search.md) |
| `executor` | 代码执行沙箱 | [docs/tools/executor.md](docs/tools/executor.md) |
| `github` | GitHub Issue 管理 | [docs/tools/github.md](docs/tools/github.md) |

---

## 🤝 贡献指南

### 提交 Issue

- 使用 GitHub Issues 提交 bug 报告或功能请求
- 提供详细的复现步骤和环境信息

### 提交 PR

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

[MIT](LICENSE) © 2024 unlimblue

---

<div align="center">

**如果这个项目对你有帮助，请给一颗 ⭐**

[⭐ Star 这个项目](https://github.com/unlimblue/ai-toolbox)

</div>
