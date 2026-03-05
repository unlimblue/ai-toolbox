# Multi-Bot System Documentation

赛博王朝多 Bot 持续对话系统文档。

---

## 文档列表

| 文档 | 说明 | 目标读者 |
|------|------|----------|
| [design.md](design.md) | 系统设计方案 | 开发者、架构师 |
| [deployment.md](deployment.md) | 部署指南 | 运维人员、用户 |
| [testing.md](testing.md) | 测试指南 | QA、开发者 |
| [debug.md](debug.md) | 调试模式说明 | 开发者、运维 |
| [research.md](research.md) | 调研报告 | 产品经理、架构师 |

---

## 快速开始

1. **部署系统**: 阅读 [deployment.md](deployment.md)
2. **测试验证**: 阅读 [testing.md](testing.md)
3. **了解架构**: 阅读 [design.md](design.md)

---

## 系统概述

**多 Bot 持续对话系统** 实现了：
- 丞相、太尉两个 AI 角色的跨频道协调
- 三层架构：Hub Listener + Message Bus + Role Bot
- 跨频道任务：金銮殿 → 内阁 → 金銮殿
- 智能上下文过滤

---

*详见各文档具体内容*