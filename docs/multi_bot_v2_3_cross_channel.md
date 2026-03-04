# 多 Bot 持续对话 - 方案 V2.3（跨频道协调）

## 新增能力：跨频道协调

### 场景示例

```
1. 皇帝在金銮殿: @丞相 @太尉，去内阁商议边防方案，回禀结果
              ↓
2. 丞相、太尉转去内阁频道继续对话
              ↓
3. 丞相、太尉在内阁相互 @ 讨论
              ↓
4. 形成结论后，返回金銮殿汇报
```

## 核心机制

### 1. 跨频道指令解析

```python
@dataclass
class CrossChannelTask:
    """跨频道任务"""
    task_id: str
    source_channel: str      # 发起频道（金銮殿）
    target_channel: str      # 执行频道（内阁）
    target_bots: list[str]   # 参与 Bot（丞相、太尉）
    instruction: str         # 任务指令
    status: str              # pending, active, completed
    created_at: datetime
    conclusion: str | None   # 结论


class CrossChannelCoordinator:
    """跨频道协调器"""
    
    def __init__(self):
        self.active_tasks: dict[str, CrossChannelTask] = {}
        self.bus: SimpleMessageBus
    
    async def parse_instruction(self, message: UnifiedMessage) -> CrossChannelTask | None:
        """解析跨频道指令"""
        content = message.content.lower()
        
        # 关键词匹配
        if "@" in message.content and any(k in content for k in ["去", "到", "在"]):
            target_channel = self.extract_channel(content)
            target_bots = message.mentions
            
            if target_channel and target_bots:
                return CrossChannelTask(
                    task_id=str(uuid.uuid4()),
                    source_channel=message.channel_id,
                    target_channel=target_channel,
                    target_bots=target_bots,
                    instruction=message.content,
                    status="pending",
                    created_at=datetime.now()
                )
        return None
```

### 2. Bot 状态机

```python
class BotState:
    """Bot 状态"""
    IDLE = "idle"              # 空闲
    DISCUSSING = "discussing"  # 讨论中（内阁）
    REPORTING = "reporting"    # 汇报中（返回金銮殿）


class StatefulBot(SimpleBotInstance):
    """带状态的 Bot"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = BotState.IDLE
        self.current_task: CrossChannelTask | None = None
        self.discussion_context: list[UnifiedMessage] = []
    
    async def handle_cross_channel_task(self, task: CrossChannelTask):
        """处理跨频道任务"""
        self.state = BotState.DISCUSSING
        self.current_task = task
        
        # 1. 在源频道确认收到任务
        await self.send_message(
            task.source_channel,
            f"领旨，即刻去{self.get_channel_name(task.target_channel)}商议。"
        )
        
        # 2. 在目标频道开始讨论
        await self.send_message(
            task.target_channel,
            f"奉陛下旨意，来此商议：{task.instruction}"
        )
    
    async def form_conclusion(self):
        """形成结论并汇报"""
        self.state = BotState.REPORTING
        
        # 生成结论
        conclusion = await self.generate_conclusion()
        
        # 在目标频道确认
        await self.send_message(
            self.current_task.target_channel,
            f"商议已定，即刻回禀陛下。"
        )
        
        # 返回源频道汇报
        await self.send_message(
            self.current_task.source_channel,
            f"启禀陛下，臣等已在{self.get_channel_name(self.current_task.target_channel)}商议完毕。\n\n结论：{conclusion}"
        )
        
        # 重置状态
        self.state = BotState.IDLE
        self.current_task = None
        self.discussion_context = []
```

## 完整场景示例

```
=== 金銮殿频道 ===
[14:00] 皇帝: @丞相 @太尉，去内阁商议边防方案，回禀结果

[14:00] 丞相: 领旨，即刻去内阁商议。
[14:00] 太尉: 遵旨。

=== 内阁频道 ===
[14:01] 丞相: 奉陛下旨意，来此商议边防方案
[14:01] 太尉: 丞相有何高见？
[14:02] 丞相: 我认为应当加强边境巡逻。
[14:03] 太尉: @丞相 同意，建议增派三千精兵。
[14:04] 丞相: @太尉 善。那我们就此定论？
[14:05] 太尉: 可。结论：加强巡逻，增兵三千。

[14:06] 丞相: 商议已定，即刻回禀陛下。
[14:06] 太尉: 回禀陛下。

=== 金銮殿频道 ===
[14:07] 丞相: 启禀陛下，臣等已在内阁商议完毕。
         结论：加强边境巡逻，增派三千精兵驻守。
[14:07] 太尉: 启禀陛下，臣赞同丞相所言。
```

## 实现要点

### 1. 跨频道检测

```python
def is_cross_channel_instruction(self, message: UnifiedMessage) -> bool:
    """检测是否为跨频道指令"""
    content = message.content.lower()
    
    # 模式：@Bot + 去/到 + 频道 + 商议/讨论
    has_mention = "@" in message.content
    has_action = any(k in content for k in ["去", "到", "在"])
    has_channel = any(k in content for k in ["内阁", "兵部", "金銮殿"])
    has_task = any(k in content for k in ["商议", "讨论", "商议", "回禀"])
    
    return has_mention and has_action and has_channel and has_task
```

### 2. 状态转换

```
IDLE -> DISCUSSING: 收到跨频道指令
DISCUSSING -> REPORTING: 形成结论
REPORTING -> IDLE: 汇报完成
```

### 3. 结论生成触发

```python
def should_form_conclusion(self) -> bool:
    """是否应该形成结论"""
    # 条件1: 讨论达到一定轮数（5轮以上）
    if len(self.discussion_context) >= 10:  # 5轮 = 10条消息
        return True
    
    # 条件2: 被 @ 且包含结论关键词
    last_msg = self.discussion_context[-1]
    if self.bot_id in last_msg.mentions:
        if any(k in last_msg.content for k in ["结论", "定论", "就这样"]):
            return True
    
    return False
```

## 实施计划

### Phase 1: 基础跨频道 (2天)
- [ ] CrossChannelTask 数据结构
- [ ] 指令解析器
- [ ] Bot 状态机

### Phase 2: 状态管理 (1天)
- [ ] IDLE -> DISCUSSING 转换
- [ ] DISCUSSING -> REPORTING 转换
- [ ] 上下文保存

### Phase 3: 完整流程 (1天)
- [ ] 金銮殿 -> 内阁 -> 金銮殿 流程
- [ ] 结论生成
- [ ] 自动汇报

### Phase 4: 测试优化 (1天)
- [ ] 三频道测试
- [ ] 边界情况处理
- [ ] 性能优化

**总计：5天**

---

*方案 V2.3 完成 - 支持跨频道协调*