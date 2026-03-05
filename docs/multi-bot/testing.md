# Cyber Dynasty Multi-Bot System - Testing Guide

## 测试概述

本系统包含三个层次的测试：
1. **单元测试** - 测试单个组件
2. **集成测试** - 测试组件间协作
3. **端到端测试** - 测试完整业务流程

---

## 快速开始

```bash
# 运行所有测试
./scripts/multi_bot.sh test

# 或手动运行
source .venv/bin/activate
pytest tests/unit/multi_bot/ tests/integration/ -v
```

---

## 单元测试

### 运行单元测试

```bash
pytest tests/unit/multi_bot/test_multi_bot.py -v
```

### 测试覆盖

| 测试类 | 测试项 | 描述 |
|--------|--------|------|
| TestModels | 3项 | 数据模型创建 |
| TestConfig | 10项 | 配置和 Prompt |
| TestMessageBus | 6项 | 消息总线功能 |
| TestRoleBot | 8项 | Bot 状态和响应 |
| TestHubListener | 3项 | Hub 监听功能 |
| TestIntegration | 2项 | 基础集成 |

### 关键测试用例

#### 1. 测试跨频道任务解析

```python
def test_cross_channel_task_parsing():
    msg = UnifiedMessage(
        content="@丞相 @太尉 去内阁商议",
        channel_id="1478759781425745940",  # 金銮殿
        mentions=["chengxiang", "taiwei"]
    )
    
    task = bus._parse_cross_channel_task(msg)
    assert task.target_channel == "1477312823817277681"  # 内阁
```

#### 2. 测试状态机转换

```python
async def test_idle_to_discussing_transition():
    bot.state == BotState.IDLE
    await bot.handle_task(task)
    assert bot.state == BotState.DISCUSSING
```

---

## 集成测试

### 运行集成测试

```bash
pytest tests/integration/test_cross_channel.py -v
```

### 测试场景

#### 场景 1：跨频道任务创建

```bash
pytest tests/integration/test_cross_channel.py::TestCrossChannelCoordination::test_cross_channel_task_creation -v
```

**验证点**：
- 皇帝在金銮殿发送跨频道指令
- MessageBus 正确创建 CrossChannelTask
- 任务包含正确的 source/target 频道

#### 场景 2：Bot 状态机

```bash
pytest tests/integration/test_cross_channel.py::TestBotStateMachine -v
```

**验证点**：
- IDLE → DISCUSSING 转换
- DISCUSSING → REPORTING 转换
- REPORTING → IDLE 转换
- 状态重置后上下文清空

#### 场景 3：完整对话流程

```bash
pytest tests/integration/test_cross_channel.py::TestCrossChannelFlow::test_full_conversation_flow -v
```

**模拟流程**：
1. 皇帝在金銮殿发起任务
2. 丞相和太尉收到任务通知
3. 在内阁进行多轮对话
4. 触发结论生成
5. 返回金銮殿汇报

---

## 端到端测试（手动）

### 测试环境准备

1. **确认 Bot 在线**
   - 在 Discord 中检查 Bot 状态
   - Hub Bot、丞相、太尉都显示在线

2. **确认频道权限**
   - Hub Bot 可以访问所有频道
   - 丞相可以访问金銮殿和内阁
   - 太尉可以访问金銮殿、内阁和兵部

### 测试用例 1：基础对话

**步骤**：
1. 在金銮殿发送：`@丞相 你好`
2. **预期**：丞相回复问候

**验证**：
- Bot 响应时间在 3 秒内
- 回复内容符合丞相角色设定

### 测试用例 2：跨频道协调

**步骤**：
1. 在金銮殿发送：`@丞相 @太尉，去内阁商议测试方案`
2. **预期**：
   - 丞相回复："领旨，即刻去内阁商议。"
   - 太尉回复："遵旨。"
   - 在内阁频道看到：
     - 丞相："奉陛下旨意，来此商议测试方案"
3. 在内阁发送：`@丞相 你觉得如何？`
4. **预期**：丞相回复建议
5. 在内阁发送：`结论：就这样定了`
6. **预期**：
   - 在内阁看到："商议已定，即刻回禀陛下。"
   - 在金銮殿看到汇报消息

### 测试用例 3：上下文保持

**步骤**：
1. 在金銮殿发送：`@丞相 记住我喜欢Python`
2. 继续对话几轮
3. 发送：`@丞相 我喜欢什么？`
4. **预期**：丞相回答"Python"

### 测试用例 4：多 Bot 协作

**步骤**：
1. 在金銮殿发送：`@丞相 @太尉，去内阁商议`
2. 在内阁观察丞相和太尉的对话
3. **预期**：
   - 两个 Bot 相互 @ 对方
   - 形成连贯的对话链条
   - 最终形成一致结论

### 测试用例 5：错误恢复

**步骤**：
1. 启动服务
2. 发送几条消息确认正常
3. 手动停止服务（模拟崩溃）
4. 重新启动服务
5. 发送消息
6. **预期**：服务正常恢复，继续工作

---

## 性能测试

### 并发测试

```bash
# 创建测试脚本
cat > test_performance.py << 'EOF'
import asyncio
from ai_toolbox.multi_bot.message_bus import MessageBus

async def test_concurrent_messages():
    bus = MessageBus()
    
    # 模拟 100 条并发消息
    tasks = []
    for i in range(100):
        msg = UnifiedMessage(...)
        tasks.append(bus.publish(msg))
    
    await asyncio.gather(*tasks)
    print(f"Processed 100 messages")

asyncio.run(test_concurrent_messages())
EOF

python test_performance.py
```

### 内存测试

```bash
# 监控内存使用
./scripts/multi_bot.sh start
watch -n 1 'ps aux | grep multi_bot | grep -v grep'
```

---

## 日志检查清单

### 正常启动日志

```
[INFO] Starting Cyber Dynasty Multi-Bot System...
[INFO] All required environment variables found
[INFO] Created and registered bot: chengxiang
[INFO] Created and registered bot: taiwei
[INFO] Starting Hub Listener...
[INFO] Hub Bot logged in as Hub#xxxx
[INFO] Monitoring 1 guild(s)
```

### 消息处理日志

```
[DEBUG] Received message from 皇帝 in #金銮殿
[INFO] Created cross-channel task: xxxxxxxx
[INFO] Bot chengxiang handling task: xxxxxxxx
[INFO] Bot taiwei handling task: xxxxxxxx
[DEBUG] Bot chengxiang added message to context
[DEBUG] Bot chengxiang sent message to 1477312823817277681
```

### 状态转换日志

```
[INFO] Bot chengxiang state: IDLE -> DISCUSSING
[INFO] Bot chengxiang triggering conclusion
[INFO] Bot chengxiang state: DISCUSSING -> REPORTING
[INFO] Completed task: xxxxxxxx
[INFO] Bot chengxiang state: REPORTING -> IDLE
```

---

## 问题诊断

### 诊断脚本

```bash
#!/bin/bash
# diagnostic.sh

echo "=== Cyber Dynasty Multi-Bot Diagnostics ==="
echo ""

echo "1. Checking process..."
ps aux | grep multi_bot | grep -v grep

echo ""
echo "2. Checking environment variables..."
if [ -f ~/.openclaw/secrets/cyber_dynasty_tokens.env ]; then
    echo "✓ Token file exists"
    ls -la ~/.openclaw/secrets/cyber_dynasty_tokens.env
else
    echo "✗ Token file missing"
fi

echo ""
echo "3. Checking logs..."
LATEST_LOG=$(ls -t logs/multi_bot_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "✓ Latest log: $LATEST_LOG"
    echo "Last 5 lines:"
    tail -n 5 "$LATEST_LOG"
else
    echo "✗ No log files found"
fi

echo ""
echo "4. Checking network..."
netstat -tlnp 2>/dev/null | grep python || ss -tlnp | grep python

echo ""
echo "5. Checking disk space..."
df -h | grep -E "(Filesystem|/root)"

echo ""
echo "6. Recent errors..."
if [ -n "$LATEST_LOG" ]; then
    grep -i "error\|exception\|failed" "$LATEST_LOG" | tail -n 5 || echo "No errors found"
fi
```

---

## 测试报告模板

```markdown
# 测试报告 - 日期

## 测试环境
- 版本: commit xxxxxx
- Python: 3.12.x
- 部署方式: systemd / 脚本

## 测试结果

### 单元测试
- [ ] 32 个测试全部通过

### 集成测试  
- [ ] 12 个测试全部通过

### 端到端测试
- [ ] 基础对话测试通过
- [ ] 跨频道协调测试通过
- [ ] 上下文保持测试通过
- [ ] 多 Bot 协作测试通过

## 发现问题

### 问题 1
- 描述: 
- 严重级别: 高/中/低
- 状态: 已修复/待修复

## 性能数据
- 平均响应时间: xx ms
- 内存使用: xx MB
- CPU 使用: xx%

## 结论
- [ ] 可以上线
- [ ] 需要修复后重新测试
```

---

## 持续集成

### GitHub Actions 配置

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run tests
        run: |
          pytest tests/unit/multi_bot/ tests/integration/ -v
      
      - name: Check coverage
        run: |
          pytest --cov=src.ai_toolbox.multi_bot --cov-report=term-missing
```