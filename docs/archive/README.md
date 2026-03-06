# 历史文档存档索引

**最后更新**: 2026-03-06

---

## 存档说明

本目录包含 AI-Toolbox 的历史设计文档和开发记录。

### 如何恢复到历史状态

如需恢复到某个历史版本：

```bash
# 查看历史提交
git log --oneline --all

# 恢复到特定提交
git checkout <commit-hash>

# 或创建分支
git checkout -b historical-branch <commit-hash>
```

---

## 存档目录

### 2026-03-06 - 自主决策架构设计

**时期**: 系统架构重大升级  
**状态**: ✅ 已完成并发布 v2.0.0

| 文档 | 说明 | 关键决策 |
|------|------|----------|
| `autonomous_architecture_design.md` | 自主决策架构完整设计 | 移除硬编码，AI自主决策 |
| `context_graph_design.md` | 有向图上下文管理设计 | 自动可见性传播 |
| `design_verification_report.md` | 设计验证报告 | 双重目标确认 |
| `hardcoded_logic_report.md` | 硬编码问题排查 | 问题根因分析 |
| `TEST_IMPROVEMENT_PLAN.md` | 测试改进计划 | 测试覆盖增强 |
| `fix_conversation_and_channel.md` | 对话连续性修复 | 多轮对话优化 |

**核心改进**:
- 从"系统解析指令"转为"AI自主决策"
- 实现Context Graph自动上下文管理
- Bot可跨频道自主执行多动作

---

### 2026-03-04 - 初始版本

**时期**: 系统初始开发  
**状态**: 📦 基础版本

**初始功能**:
- 基础Multi-Bot系统
- Hub + MessageBus + RoleBot架构
- 跨频道任务处理
- Context Filter基础实现

---

## 快速导航

- **当前版本文档**: 见 `docs/` 根目录
- **架构设计**: `docs/ARCHITECTURE.md`
- **部署指南**: `docs/DEPLOYMENT.md`
- **项目主页**: `README.md`

---

## 标签对应

| 版本 | 标签 | 说明 |
|------|------|------|
| v2.0.0 | `v2.0.0` | 自主决策架构发布 |

---

*历史存档，供参考使用*
