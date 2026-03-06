# 测试改进计划

**日期**: 2026-03-06  
**问题**: API 变更导致 main.py 调用失败

---

## 事故分析

### 问题
- 重构 RoleBot 时修改了 `__init__` 签名
- 未同步更新 `main.py` 的调用代码
- 单元测试未覆盖到 main.py 的集成路径

### 根本原因
1. **测试覆盖不足**: 现有单元测试只测试单个组件，未测试组件集成
2. **缺乏集成测试**: 没有端到端的启动流程测试
3. **API 变更未同步**: 修改接口时未检查所有调用点

---

## 改进措施

### 立即执行 (今天)

1. **添加集成测试**
```python
# tests/integration/test_main_startup.py
def test_create_bot_from_config():
    """Test bot creation with new API"""
    from ai_toolbox.multi_bot.main import create_bot_from_config
    from ai_toolbox.multi_bot.graph_manager import ContextGraphManager
    
    config = get_config()
    graph_manager = ContextGraphManager()
    
    bot = create_bot_from_config("chengxiang", config, graph_manager)
    assert bot is not None
    assert bot.bot_id == "chengxiang"
```

2. **添加启动流程测试**
```python
# tests/integration/test_startup.py
@pytest.mark.asyncio
async def test_main_startup():
    """Test full startup sequence"""
    # Mock environment and test startup
```

### 短期 (本周)

3. **API 变更检查清单**
   - 修改接口时检查所有调用点
   - 更新调用点前先标记 TODO
   - 使用 IDE 的 "Find Usages" 功能

4. **自动化集成测试**
   - CI/CD 中添加启动测试
   - 每次提交都运行集成测试
   - 失败时阻止合并

### 长期 (本月)

5. **契约测试**
   - 定义组件间 API 契约
   - 契约变更时自动提醒
   - 使用类型检查工具 (mypy)

6. **端到端测试**
   - 模拟 Discord 消息
   - 验证完整对话流程
   - 每日自动运行

---

## 实施时间

- **今天**: 添加基础集成测试
- **本周**: 完善测试覆盖
- **持续**: 严格执行检查清单

---

*臣失职，即刻改进*
