# 设计验证报告：无硬编码 + Context Graph 自动识别

**验证日期**: 2026-03-06  
**验证人**: AI Assistant  
**状态**: ✅ 通过

---

## 1. 验证目标

确认新架构设计同时满足：
1. ✅ **无硬编码**: 没有指令解析、频道映射、任务类型判断等硬编码逻辑
2. ✅ **Context Graph 自动识别**: 自动计算可见性、自动提取相关上下文

---

## 2. 无硬编码验证

### 2.1 MessageBus 层

| 检查项 | 旧代码 | 新设计 | 状态 |
|--------|--------|--------|------|
| 频道别名映射 | `channel_aliases = {"金銮殿": "jinluan"...}` | ❌ 完全移除 | ✅ |
| 指令解析 | `_parse_cross_channel_task()` 硬编码匹配 | ❌ 完全移除 | ✅ |
| 任务类型判断 | 根据关键词判断任务类型 | ❌ 不做任何判断 | ✅ |
| 目标 Bot 选择 | 代码解析内容中的 Bot 名称 | ❌ 只转发被@的 Bot | ✅ |

**新 MessageBus.publish()**:
```python
async def publish(self, message: UnifiedMessage):
    # 1. 添加到 ContextGraph（无解析）
    graph_id = self._get_graph_id(message.channel_id)
    self.graph_manager.add_message(graph_id, message)
    
    # 2. 转发给被 @ 的 Bot（无解析）
    for bot_id in message.mentions:
        if bot_id in self.role_bots:
            await self.role_bots[bot_id].handle_message(message, graph_id)
```

**结论**: ✅ MessageBus 无任何硬编码解析逻辑

---

### 2.2 ContextGraph 层

| 检查项 | 旧代码 | 新设计 | 状态 |
|--------|--------|--------|------|
| 频道匹配逻辑 | 硬编码别名映射 | ❌ 完全移除 | ✅ |
| 消息类型判断 | 判断是否为任务消息 | ❌ 不做类型判断 | ✅ |
| 可见性规则 | 基于代码规则 | ✅ 基于图传播算法 | ✅ |

**可见性计算**（自动，非硬编码）:
```python
def _calculate_visibility(self, graph: ContextGraph, node: MessageNode):
    """
    自动计算，基于图结构传播：
    - 被 @ 的 Bot 可见
    - 父消息可见者，子消息也可见
    - 不依赖硬编码规则
    """
    visible = set()
    visible.add(node.author_id)
    visible.update(node.mention_targets)
    
    # 从父节点继承可见性
    for parent_id in node.parents:
        if parent_id in graph.nodes:
            visible.update(graph.nodes[parent_id].visible_to)
    
    node.visible_to = visible
```

**结论**: ✅ ContextGraph 无硬编码，可见性自动计算

---

### 2.3 RoleBot 层

| 检查项 | 旧代码 | 新设计 | 状态 |
|--------|--------|--------|------|
| 频道名称映射 | `_get_channel_name()` 硬编码ID映射 | ❌ 从配置读取 | ✅ |
| 开场白模板 | 硬编码字符串 | ❌ AI 自主生成 | ✅ |
| 动作格式 | 强制 `[ACTION: type]` | ❌ AI 自主决定格式 | ✅ |
| 任务处理 | `handle_task()` 固定流程 | ❌ 统一 `handle_message()` | ✅ |

**新 RoleBot**:
```python
async def handle_message(self, message: UnifiedMessage, graph_id: str):
    # 获取上下文（自动）
    context = self.graph_manager.get_context_for_bot(graph_id, self.bot_id)
    
    # AI 自主决策（无硬编码）
    decision_prompt = self._build_decision_prompt(message, context)
    actions = await self._ai_decide(decision_prompt)
    
    # 执行动作（AI 决定）
    for action in actions:
        await self._execute_action(action)
```

**结论**: ✅ RoleBot 无硬编码逻辑，完全由 AI 决策

---

## 3. Context Graph 自动识别验证

### 3.1 自动可见性计算

**场景**: 用户 @丞相 去内阁通知太尉

```
消息图（金銮殿）:
    用户: "@丞相 去内阁通知太尉"
         │
         ├── 可见: [丞相] (被@)
         │
         └── 后续传播:
             丞相在内阁的消息 ──► 可见: [丞相, 太尉]
```

**自动传播**:
1. 初始: 用户消息可见给丞相
2. 丞相转发给太尉: 太尉看到丞相的消息
3. 无需硬编码规则，纯图传播

**结论**: ✅ 可见性自动计算和传播

---

### 3.2 上下文自动提取

**场景**: 太尉在内阁收到丞相的消息

```python
# ContextGraph 自动提取
def get_context_for_bot(self, graph_id: str, bot_id: str, limit: int = 20):
    graph = self.graphs.get(graph_id)
    
    # 自动提取可见节点
    visible_nodes = {
        node_id for node_id, node in graph.nodes.items()
        if bot_id in node.visible_to  # 自动判断
    }
    
    # 自动拓扑排序
    sorted_nodes = self._topological_sort(visible_nodes)
    
    return SubGraph(nodes=visible_nodes, sorted_order=sorted_nodes)
```

**结论**: ✅ 上下文自动提取，Bot 只看到相关消息

---

### 3.3 跨频道上下文合并

**场景**: 丞相从金銮殿去内阁

```
金銮殿图:                    内阁图:
  用户: "@丞相 去内阁..."      丞相: "@太尉 请前来"
       │                           │
       └── 合并 ───────────────────┘
              │
              ▼
        丞相的完整上下文:
        - 金銮殿: 用户指令
        - 内阁: 当前对话
```

**自动合并**:
```python
def get_multi_channel_context(self, bot_id: str, channel_ids: List[str]):
    contexts = {}
    for channel_id in channel_ids:
        graph_id = f"channel_{channel_id}"
        contexts[channel_id] = self.get_context_for_bot(graph_id, bot_id)
    return contexts
```

**结论**: ✅ 跨频道上下文自动合并

---

## 4. 综合验证

### 4.1 场景测试

**指令**: "@丞相 去内阁通知太尉，来金銮殿回话"

| 步骤 | 旧架构（硬编码） | 新架构（自主决策） |
|------|-----------------|-------------------|
| 1. 系统解析 | ❌ 硬编码匹配"内阁"、"金銮殿" | ✅ 无解析，直接转发 |
| 2. 任务创建 | ❌ 硬编码创建 CrossChannelTask | ✅ 无任务概念 |
| 3. 上下文准备 | ⚠️ 基于任务ID获取 | ✅ 自动从 ContextGraph 提取 |
| 4. 决策 | ❌ 硬编码动作序列 | ✅ AI 自主决策 |
| 5. 执行 | ❌ 硬编码频道和内容 | ✅ AI 决定频道、@、内容 |

---

### 4.2 代码对比

#### 旧代码（有硬编码）
```python
# message_bus.py - 硬编码频道别名
channel_aliases = {
    "金銮殿": "jinluan",
    "内阁": "neige",
    "兵部": "bingbu",
}

# 硬编码解析逻辑
if "内阁" in content:
    target_channel_id = "1477312823817277681"

# role_bot.py - 硬编码开场白
await self.send_message(
    task.target_channel,
    f"臣已至{target_channel_name}，请{other_bot_name}前来会合。"
)
```

#### 新设计（无硬编码）
```python
# message_bus.py - 无解析
def publish(self, message):
    self.graph_manager.add_message(graph_id, message)  # 只存储
    for bot_id in message.mentions:  # 只转发
        await self.role_bots[bot_id].handle_message(message, graph_id)

# role_bot.py - AI 自主决策
async def handle_message(self, message, graph_id):
    context = self.graph_manager.get_context_for_bot(graph_id, self.bot_id)
    actions = await self._ai_decide(context)  # AI 决定一切
    for action in actions:
        await self.send_message(action.channel_id, action.content)
```

---

## 5. 验证结论

### 5.1 无硬编码 ✅

| 组件 | 硬编码内容 | 状态 |
|------|-----------|------|
| MessageBus | ❌ 无频道别名、无指令解析、无任务创建 | ✅ |
| ContextGraph | ❌ 无频道匹配、无类型判断 | ✅ |
| RoleBot | ❌ 无开场白模板、无固定动作序列 | ✅ |
| System Prompt | ✅ 只有示例说明，非强制规则 | ✅ |

### 5.2 Context Graph 自动识别 ✅

| 能力 | 实现方式 | 状态 |
|------|---------|------|
| 可见性计算 | 图传播算法（自动） | ✅ |
| 上下文提取 | 子图提取算法（自动） | ✅ |
| 跨频道合并 | 多图合并（自动） | ✅ |
| 分支/合并支持 | DAG 结构（自动） | ✅ |

### 5.3 双重目标达成 ✅

**无硬编码**: 所有决策由 AI 自主完成，系统只做消息路由和上下文管理  
**Context Graph**: 自动计算可见性、自动提取上下文、保证对话连贯性

---

## 6. 最终确认

✅ **设计通过验证**  
✅ **可以同时实施**  
✅ **等待实施指令**

---

*验证完成时间: 2026-03-06 02:40*
