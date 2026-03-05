# AI-Toolbox Documentation

本文档目录包含 AI-Toolbox 项目的完整文档。

---

## 目录结构

```
docs/
├── README.md                    # 本文档 - 导航入口
├── architecture.md              # 系统架构设计
│
├── multi-bot/                   # 多 Bot 系统文档
│   ├── README.md               # 多 Bot 系统概览
│   ├── design.md               # 最终设计方案
│   ├── deployment.md           # 部署指南
│   ├── testing.md              # 测试指南
│   ├── debug.md                # 调试模式说明
│   └── research.md             # 调研报告
│
├── archive/                     # 历史归档
│   └── 2026-03-04.md           # 项目状态存档
│
└── development/                 # 开发过程文档
    └── implementation_plan_fix.md  # 修复实施计划

```

---

## 快速导航

### 对于用户

| 需求 | 文档 |
|------|------|
| 了解系统架构 | [architecture.md](architecture.md) |
| 部署多 Bot 系统 | [multi-bot/deployment.md](multi-bot/deployment.md) |
| 测试多 Bot 系统 | [multi-bot/testing.md](multi-bot/testing.md) |

### 对于开发者

| 需求 | 文档 |
|------|------|
| 了解设计方案 | [multi-bot/design.md](multi-bot/design.md) |
| 调试系统 | [multi-bot/debug.md](multi-bot/debug.md) |
| 查看调研背景 | [multi-bot/research.md](multi-bot/research.md) |

### 历史记录

| 文档 | 说明 |
|------|------|
| [archive/2026-03-04.md](archive/2026-03-04.md) | 项目状态存档 |
| [development/implementation_plan_fix.md](development/implementation_plan_fix.md) | 修复实施计划 |

---

## 核心文档说明

### 1. 系统架构 (architecture.md)
- AI-Toolbox 整体架构
- 模块划分和职责
- 数据流图

### 2. 多 Bot 系统设计 (multi-bot/design.md)
- 三层架构设计
- System Prompt 设计
- 跨频道协调机制
- Token 安全方案

### 3. 部署指南 (multi-bot/deployment.md)
- 环境准备
- Token 配置
- 启动方式（脚本/systemd）
- 故障排除

### 4. 测试指南 (multi-bot/testing.md)
- 单元测试
- 集成测试
- 端到端测试
- 性能测试

### 5. 调试模式 (multi-bot/debug.md)
- Debug 模式原理
- 调试消息格式
- 上下文隔离机制

---

## 使用建议

1. **首次使用**: 阅读 [multi-bot/deployment.md](multi-bot/deployment.md) 完成部署
2. **遇到故障**: 查看 [multi-bot/debug.md](multi-bot/debug.md) 进行排查
3. **开发扩展**: 参考 [multi-bot/design.md](multi-bot/design.md) 了解架构

---

*最后更新: 2026-03-05*