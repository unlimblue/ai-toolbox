# Context Graph 增强型自主决策架构设计

**日期**: 2026-03-06  
**目标**: 移除硬编码解析，保留 Context Graph 能力，实现 Bot 完全自主决策

---

## 1. 核心设计理念

### 1.1 原则

**系统职责**: 只做消息路由和上下文管理  
**Bot 职责**: 自主理解决策，包括频道选择、@对象、回复内容

### 1.2 关键分离

| 层级 | 职责 | 不做什么 |
|------|------|----------|
| **MessageBus** | 消息路由、Context Graph 维护 | 不解析指令、不创建任务 |
| **ContextGraph** | 存储对话历史、计算可见性、提取子图 | 不决策、不干预 |
| **RoleBot** | 接收消息+上下文、AI 决策、执行动作 | 不硬编码逻辑 |

---

## 2. 架构设计

### 2.1 数据流

```
用户消息
    ↓
HubListener (Discord → UnifiedMessage)
    ↓
MessageBus.publish(message)
    ├── 添加到 ContextGraph (按频道)
    └── 转发给被 @ 的 Bot
                ↓
        RoleBot.handle_message(message)
            ├── 获取完整上下文 (从 ContextGraph)
            ├── AI 自主决策
            │   ├── 理解指令意图
            │   ├── 决定响应频道
            │   ├── 决定 @ 对象
            │   └── 生成回复内容
            └── 执行动作
                ├── send_message(频道A, 内容A)
                ├── send_message(频道B, 内容B)
                └── ...
```

### 2.2 Context Graph 角色

**核心功能**: 
- 存储所有消息的完整历史
- 计算消息可见性（谁能看到什么）
- 为 Bot 提取相关上下文子图

**不干预决策**:
- 不决定 Bot 该做什么
- 不限制 Bot 的选择
- 只提供上下文数据

---

## 3. 关键组件设计

### 3.1 MessageBus (简化版)

```python
class MessageBus:
    """
    只做两件事：
    1. 维护 ContextGraph
    2. 路由消息给 Bot
    """
    
    def __init__(self):
        self.graph_manager = ContextGraphManager()
        self.role_bots = {}  # bot_id -> RoleBot
    
    async def publish(self, message: UnifiedMessage):
        """
        发布消息：添加到图，然后转发
        """
        # 1. 添加到 ContextGraph
        graph_id = self._get_graph_id(message.channel_id)
        self.graph_manager.add_message(graph_id, message)
        
        # 2. 转发给被 @ 的 Bot（不做任何解析）
        for bot_id in message.mentions:
            if bot_id in self.role_bots:
                # 传递消息 + 图引用
                await self.role_bots[bot_id].handle_message(
                    message, 
                    graph_id=graph_id
                )
    
    def _get_graph_id(self, channel_id: str) -> str:
        """每个频道一个图"""
        return f"channel_{channel_id}"
```

### 3.2 ContextGraphManager (核心)

```python
class ContextGraphManager:
    """
    管理所有对话图
    """
    
    def __init__(self):
        self.graphs: Dict[str, ContextGraph] = {}
    
    def get_or_create_graph(self, graph_id: str) -> ContextGraph:
        if graph_id not in self.graphs:
            self.graphs[graph_id] = ContextGraph(graph_id)
        return self.graphs[graph_id]
    
    def add_message(self, graph_id: str, message: UnifiedMessage):
        """添加消息到图，自动计算可见性"""
        graph = self.get_or_create_graph(graph_id)
        node = graph.add_message(message)
        
        # 计算可见性（传播给 @ 的人）
        self._calculate_visibility(graph, node)
    
    def get_context_for_bot(self, graph_id: str, bot_id: str, 
                           limit: int = 20) -> SubGraph:
        """
        为 Bot 提取相关上下文
        只提取对该 Bot 可见的消息
        """
        graph = self.graphs.get(graph_id)
        if not graph:
            return SubGraph()
        
        return graph.extract_subgraph(bot_id, limit)
    
    def get_multi_channel_context(self, bot_id: str, 
                                   channel_ids: List[str],
                                   limit: int = 20) -> Dict[str, SubGraph]:
        """
        获取多个频道的上下文
        用于 Bot 跨频道决策
        """
        contexts = {}
        for channel_id in channel_ids:
            graph_id = f"channel_{channel_id}"
            contexts[channel_id] = self.get_context_for_bot(
                graph_id, bot_id, limit
            )
        return contexts
```

### 3.3 RoleBot (自主决策版)

```python
class RoleBot:
    """
    完全自主决策的 Bot
    """
    
    def __init__(self, config: BotConfig, graph_manager: ContextGraphManager):
        self.config = config
        self.graph_manager = graph_manager
        self.bot_id = config.bot_id
    
    async def handle_message(self, message: UnifiedMessage, graph_id: str):
        """
        处理消息：获取上下文，AI 决策，执行动作
        """
        # 1. 获取完整上下文
        context = self.graph_manager.get_context_for_bot(
            graph_id, self.bot_id, limit=20
        )
        
        # 2. 构建决策 Prompt
        decision_prompt = self._build_decision_prompt(message, context)
        
        # 3. AI 自主决策
        actions = await self._ai_decide(decision_prompt)
        
        # 4. 执行所有动作
        for action in actions:
            await self._execute_action(action)
    
    def _build_decision_prompt(self, message: UnifiedMessage, 
                               context: SubGraph) -> str:
        """
        构建让 AI 自主决策的 Prompt
        """
        # 获取所有可用频道
        available_channels = self._get_available_channels()
        
        return f"""你收到了一条消息，需要自主决定如何响应。

## 你的信息
- 身份: {self.config.persona.name}
- 位置: {self._get_current_location()}

## 收到的消息
来自: {message.author_name}
内容: {message.content}

## 对话上下文
{context.format_history()}

## 可用频道
{self._format_channels(available_channels)}

## 协作 Bot
{self._format_other_bots()}

## 决策指南

你需要自主决定:

1. **在哪响应**: 
   - 可以在当前频道回复
   - 可以去其他频道（如果需要）
   - 可以同时在多个频道发送消息

2. **@谁**:
   - 如果需要其他 Bot 参与，使用 `@Bot名` 或 `\u003c@\u0026ROLE_ID\u003e`
   - 不要 @ 自己

3. **说什么**:
   - 自然、简洁、符合你的身份
   - 如果需要多轮对话，说明下一步计划

## 输出格式

用 JSON 格式输出你的行动计划:

```json
{{
  "actions": [
    {{
      "channel_id": "频道ID",
      "channel_name": "频道名称",
      "content": "消息内容（可以包含 @）",
      "reason": "为什么在这个频道发送"
    }}
  ],
  "plan": "简要说明你的整体计划"
}}
```

如果只做一个动作，actions 数组只有一个元素。
如果不需响应，返回空数组。
"""
    
    async def _ai_decide(self, prompt: str) -> List[BotAction]:
        """
        调用 AI，解析决策结果
        """
        client = create_provider(...)
        
        messages = [
            ChatMessage(role="system", content=self.config.persona.system_prompt),
            ChatMessage(role="user", content=prompt)
        ]
        
        response = await client.chat(messages)
        
        # 解析 JSON 动作
        return self._parse_actions_json(response.content)
    
    async def _execute_action(self, action: BotAction):
        """执行单个动作"""
        await self.send_message(action.channel_id, action.content)
        
        # 可选：添加自己的消息到 ContextGraph
        self._add_own_message_to_graph(action)
    
    def _get_available_channels(self) -> List[ChannelInfo]:
        """获取 Bot 可以访问的所有频道"""
        # 从配置读取
        return [
            ChannelInfo(id="1478759781425745940", name="金銮殿", type="source"),
            ChannelInfo(id="1477312823817277681", name="内阁", type="target"),
            ChannelInfo(id="1477273291528867860", name="兵部", type="target"),
        ]
```

---

## 4. System Prompt 增强

### 4.1 新增内容 (config/multi_bot.yaml)

```yaml
persona:
  custom_instructions: |
    ## 自主决策指南
    
    你拥有完全的自主权，系统不会干预你的决策。
    
    ### 频道选择
    
    你可以自主选择在哪个频道发送消息：
    
    | 频道 | 用途 |
    |------|------|
    | 金銮殿 | 皇帝所在，用于汇报、接收指令 |
    | 内阁 | 商议事务，与其他 Bot 讨论 |
    | 兵部 | 军事防务相关 |
    
    **示例决策**:
    - 用户说"去内阁通知太尉" → 你应该在内阁 @太尉
    - 用户说"来金銮殿回话" → 你应该在金銮殿回复
    - 用户说"通知太尉来金銮殿" → 在内阁 @太尉，然后回金銮殿汇报
    
    ### @ 格式
    
    - 丞相: `\u003c@\u00261477314769764614239\u003e`
    - 太尉: `\u003c@\u00261478217215936430092\u003e`
    
    ### 协作规范
    
    - 收到指令后，自主判断是否需其他 Bot 配合
    - 需要配合时，主动 @ 相关 Bot
    - 对话结束后，回到金銮殿汇报
```

---

## 5. 复杂场景处理

### 5.1 场景: "@丞相 去内阁通知太尉，来金銮殿回话"

**系统行为**:
1. Hub 收到消息，转发给 MessageBus
2. MessageBus 添加到金銮殿的 ContextGraph
3. MessageBus 转发给丞相

**丞相自主决策**:
```json
{
  "actions": [
    {
      "channel_id": "1477312823817277681",
      "channel_name": "内阁",
      "content": "\u003c@\u00261478217215936430092\u003e 太尉大人，陛下召您前往金銮殿。",
      "reason": "先去内阁通知太尉"
    },
    {
      "channel_id": "1478759781425745940",
      "channel_name": "金銮殿",
      "content": "启禀陛下，臣已通知太尉，即刻前来。",
      "reason": "回金銮殿汇报"
    }
  ],
  "plan": "先去内阁通知太尉，然后回金銮殿向皇帝汇报"
}
```

### 5.2 场景: "@丞相 @太尉 去内阁商议"

**丞相决策**:
```json
{
  "actions": [
    {
      "channel_id": "1477312823817277681",
      "channel_name": "内阁",
      "content": "\u003c@\u00261478217215936430092\u003e 太尉大人，请前来商议要事。",
      "reason": "在内阁召集太尉"
    }
  ]
}
```

### 5.3 场景: 太尉在内阁收到丞相的消息

**系统行为**:
1. 丞相在内阁的消息添加到内阁 ContextGraph
2. 消息通过 @ 转发给太尉
3. 太尉获取内阁的上下文（包含丞相的消息）

**太尉决策**:
```json
{
  "actions": [
    {
      "channel_id": "1477312823817277681",
      "channel_name": "内阁",
      "content": "\u003c@\u00261477314769764614239\u003e 丞相大人，臣已至，请吩咐。",
      "reason": "在内阁回应丞相"
    }
  ]
}
```

---

## 6. Context Graph 保证

### 6.1 可见性保证

- **消息只被相关 Bot 看到**
- **跨频道对话历史连贯**
- **支持分支和合并场景**

### 6.2 性能保证

- **按需提取子图**，不加载无关消息
- **缓存机制**，加速重复查询
- **自动清理旧数据**

---

## 7. 实施步骤

### 阶段 1: 重构 MessageBus
- [ ] 移除 `_parse_cross_channel_task`
- [ ] 简化 `publish` 方法
- [ ] 确保正确维护 ContextGraph

### 阶段 2: 重构 RoleBot
- [ ] 移除 `handle_task`
- [ ] 实现 `_build_decision_prompt`
- [ ] 实现 `_ai_decide` JSON 解析

### 阶段 3: 增强 System Prompt
- [ ] 添加频道选择说明
- [ ] 添加决策示例
- [ ] 添加 @ 格式参考

### 阶段 4: 测试验证
- [ ] 测试单频道对话
- [ ] 测试跨频道任务
- [ ] 测试多 Bot 协作
- [ ] 验证 Context Graph 正确性

---

## 8. 风险控制

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI 不遵循 JSON 格式 | 高 | 添加格式示例，失败时重试 |
| AI 选择错误频道 | 中 | Prompt 中清晰说明频道用途 |
| AI 忘记 @ 对象 | 中 | Prompt 中强调协作对象 |
| Context Graph 过大 | 低 | 自动清理旧消息 |

---

## 9. 总结

**新架构优势**:
1. **无硬编码**: 所有决策由 AI 自主完成
2. **保留 Context Graph**: 保证上下文连贯性
3. **灵活可扩展**: 新增频道/Bot 无需改代码
4. **自然交互**: Bot 像人类一样对话

**关键设计**:
- 系统只路由消息和维护图
- Bot 自主理解决策执行
- Context Graph 提供上下文支持

---

*设计完成，等待实施指令*
