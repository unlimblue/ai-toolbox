# 测试说明 - 自主决策架构

**日期**: 2026-03-06

## 状态

### 新架构测试
- ✅ `test_autonomous_architecture.py`: 5个测试通过，3个需调整

### 旧测试兼容性
- ⚠️ 部分旧测试与新架构 API 不兼容
- ⚠️ 需要逐步迁移

## 不兼容的变更

| 旧 API | 新 API | 说明 |
|--------|--------|------|
| `MessageBus.register_bot(bot_id)` | `MessageBus.register_bot(bot_id, bot_instance)` | 需要传入实例 |
| `RoleBot.handle_task(task)` | `RoleBot.handle_message(message, graph_id)` | 统一入口 |
| `RoleBot._is_relevant()` | 已移除 | 不再使用 |
| `RoleBot._should_respond()` | 已移除 | 由 AI 决定 |
| `RoleBot._parse_cross_channel_task()` | 已移除 | 无硬编码解析 |

## 运行测试

```bash
# 只运行新架构测试
python -m pytest tests/unit/multi_bot/test_autonomous_architecture.py -v

# 运行所有测试（部分会失败）
python -m pytest tests/ -v
```

## 建议

旧测试需要逐步迁移到新架构。核心功能已通过新测试验证。
