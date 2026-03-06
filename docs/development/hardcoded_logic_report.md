# 硬编码逻辑排查报告及解决方案

**日期**: 2026-03-06  
**状态**: 根本性重构 - 移除硬编码，完全由 Agent 自主控制

---

## 1. 当前问题

### 1.1 核心矛盾

**当前架构**: 代码硬编码解析用户指令中的频道、Bot、动作  
**目标架构**: Agent 通过 System Prompt 理解指令，自主选择频道和动作

### 1.2 已发现的硬编码问题

| 位置 | 硬编码内容 | 问题 |
|------|-----------|------|
| `message_bus.py:180-210` | 频道别名映射 | 无法灵活处理新频道 |
| `message_bus.py:220-260` | `_parse_cross_channel_task` | 硬编码解析逻辑，容易误判 |
| `role_bot.py:400-500` | `handle_task` 多动作 Prompt | 复杂的 ACTION 格式要求 |
| `role_bot.py:500-550` | `_parse_actions` | 硬编码解析 AI 响应格式 |
| `role_bot.py:720-730` | `_get_channel_name` | 硬编码频道 ID 映射 |

---

## 2. 根本原因分析

### 2.1 设计哲学冲突

**旧设计**: 系统理解用户指令 → 创建任务 → 分配给 Bot → Bot 执行  
**问题**: 系统理解可能与用户意图不符

**新设计**: 系统只转发消息 → Bot 自己理解指令 → Bot 自主决策 → Bot 执行  
**优势**: Bot 基于完整上下文做出最佳决策

### 2.2 具体问题

1. **频道解析歧义**
   - 用户: "去内阁通知太尉，来金銮殿回话"
   - 系统: 找到"金銮殿"（源频道），任务创建失败
   - 应该: Bot 自己理解要去内阁

2. **多动作复杂性**
   - 当前: 要求 AI 输出 `[ACTION: type]` 格式
   - 问题: AI 经常不遵循格式
   - 应该: AI 自然表达，系统不强制格式

3. **任务概念过度设计**
   - 当前: 复杂的 CrossChannelTask 对象
   - 问题: 限制 Bot 自主性
   - 应该: Bot 自主决定去哪里、@谁

---

## 3. 解决方案

### 3.1 核心原则

**单一原则**: 系统只做消息转发，所有决策由 Bot 自主完成  
**Channel**: Bot 自主选择发送频道  
**Content**: Bot 自主生成回复内容  
**Mentions**: Bot 自主决定 @ 谁

### 3.2 架构简化

```
旧架构:
用户消息 → Hub → MessageBus解析任务 → 创建CrossChannelTask → 分配给Bot → Bot执行固定动作

新架构:
用户消息 → Hub → 直接转发给被@的Bot → Bot自主理解 → Bot自主选择频道发送 → Bot自主生成内容
```

### 3.3 具体修改方案

#### 修改 1: 简化消息处理流程

**文件**: `message_bus.py`  
**操作**: 删除 `_parse_cross_channel_task`，直接转发消息

```python
# 旧代码
async def publish(self, message: UnifiedMessage):
    task = self._parse_cross_channel_task(message)
    if task:
        for bot_id in task.target_bots:
            await self.role_bots[bot_id].handle_task(task)
    else:
        await self._distribute_message(message)

# 新代码  
async def publish(self, message: UnifiedMessage):
    # 直接转发给被@的 Bot，不做任何解析
    for bot_id in message.mentions:
        if bot_id in self.role_bots:
            await self.role_bots[bot_id].handle_message(message)
```

#### 修改 2: 增强 System Prompt

**文件**: `config/multi_bot.yaml`  
**操作**: 在 `persona.custom_instructions` 中添加频道自主选择权

```yaml
custom_instructions: |
  ## 自主频道选择
  
  你可以自主选择在哪个频道发送消息：
  - 如果用户说"去内阁通知太尉"，你应该在内阁 @太尉
  - 如果用户说"来金銮殿回话"，你应该在金銮殿回复
  - 你可以同时在多个频道发送消息（如果需要）
  
  ## 可用频道
  - 金銮殿 (jinluan): 皇帝所在，用于汇报
  - 内阁 (neige): 商议事务
  - 兵部 (bingbu): 军事防务
  
  ## 行动指南
  1. 理解用户指令中的地点要求
  2. 自主决定去哪里、@谁、说什么
  3. 使用 `<@&ROLE_ID>` 格式 @ 其他 Bot
```

#### 修改 3: 简化 RoleBot 处理逻辑

**文件**: `role_bot.py`  
**操作**: 删除 `handle_task` 和 `_parse_actions`，统一使用 `handle_message`

```python
# 删除复杂的 handle_task 方法
# 统一使用简单的 handle_message:

async def handle_message(self, message: UnifiedMessage):
    # 直接生成响应
    response = await self._generate_response(message)
    
    # 让 AI 自己决定在哪个频道发送
    # 通过 Prompt 引导 AI 输出频道选择
```

#### 修改 4: 简化响应生成

**文件**: `role_bot.py`  
**操作**: `_generate_response` 只负责生成内容，不强制格式

```python
async def _generate_response(self, message: UnifiedMessage) -> Optional[str]:
    prompt = f"""
    用户指令：{message.content}
    当前频道：{self._get_channel_name(message.channel_id)}
    
    请直接回复，自然表达你的想法。
    如果需要去其他频道，请在回复中说明。
    """
    
    response = await client.chat(messages)
    return response.content
```

---

## 4. 实施计划

### 阶段 1: 移除硬编码频道解析 (立即)
- [ ] 删除 `message_bus.py` 中的 `_parse_cross_channel_task`
- [ ] 简化 `publish` 方法直接转发
- [ ] 更新 `role_bot.py` 移除 `handle_task`

### 阶段 2: 增强 System Prompt (立即)
- [ ] 更新 `config/multi_bot.yaml` 添加频道选择说明
- [ ] 添加 Bot 协作指南
- [ ] 添加示例对话

### 阶段 3: 简化 RoleBot 逻辑 (立即)
- [ ] 删除 `_parse_actions` 方法
- [ ] 简化 `_generate_response`
- [ ] 删除 `_get_channel_name` 硬编码映射

### 阶段 4: 测试验证 (后续)
- [ ] 测试单 Bot 响应
- [ ] 测试多 Bot 协作
- [ ] 测试跨频道对话

---

## 5. 预期效果

### 5.1 用户指令示例

**指令**: "@丞相 去内阁通知太尉，来金銮殿回话"

**丞相自主行为**:
1. 理解要去内阁通知太尉
2. 在内阁 @太尉: "太尉大人，陛下召您去金銮殿"
3. 在金銮殿回复: "启禀陛下，已通知太尉"

**完全由 AI 自主完成，无硬编码干预！**

### 5.2 优势

| 方面 | 效果 |
|------|------|
| 灵活性 | 支持任意复杂指令，无需预设模式 |
| 可扩展 | 新增频道无需修改代码 |
| 自然性 | AI 自主决策，更像人类对话 |
| 健壮性 | 不依赖固定格式，容错性高 |

---

## 6. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI 不理解指令 | 高 | 增强 System Prompt，添加示例 |
| AI 不 @ 正确 Bot | 中 | Prompt 中强调 @ 格式和协作对象 |
| AI 选择错误频道 | 中 | Prompt 中清晰说明频道用途 |
| 响应时间增加 | 低 | AI 只需要一次推理 |

---

## 7. 后续优化方向

1. **上下文学习**: 根据历史对话调整 Bot 行为
2. **多轮规划**: 支持复杂多步骤任务规划
3. **自适应**: Bot 根据反馈自我调整

---

**报告生成时间**: 2026-03-06 02:30  
**下一步**: 等待陛下批准后实施重构
