# AI-Toolbox 文档中心

欢迎来到 AI-Toolbox 文档中心！

---

## 📚 核心文档

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目主页，快速开始 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构详细设计 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署指南 |
| [TEST_CASES.md](TEST_CASES.md) | 测试用例 |

---

## 📁 目录结构

```
docs/
├── README.md                 # 本文档
├── ARCHITECTURE.md           # 架构设计
├── DEPLOYMENT.md             # 部署指南
├── TEST_CASES.md            # 测试用例
├── multi-bot/               # 多 Bot 相关
│   ├── deployment.md
│   ├── design.md
│   ├── testing.md
│   └── debug.md
├── archive/                 # 历史归档
│   └── 2026-03-06/         # 历史设计文档
└── development/             # 开发文档
    └── TEST_IMPROVEMENT_PLAN.md
```

---

## 🚀 快速导航

### 新用户
1. 阅读 [README.md](../README.md) 了解项目
2. 跟随 [DEPLOYMENT.md](DEPLOYMENT.md) 部署
3. 查看 [TEST_CASES.md](TEST_CASES.md) 测试

### 开发者
1. 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 理解架构
2. 查看 `multi-bot/` 目录了解子系统
3. 参考 `archive/` 了解演进历史

---

## 📖 设计理念

AI-Toolbox 采用**自主决策架构**：

- **无硬编码**: 系统不解析指令，AI 自主决策
- **Context Graph**: 自动维护对话上下文
- **配置驱动**: 通过 YAML 定义角色，无需改代码

---

*最后更新: 2026-03-06*
