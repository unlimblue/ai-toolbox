# 赛博王朝多 Bot 持续对话系统 - 最终设计方案

## 概述

本方案实现赛博王朝 Discord 服务器的多 Bot 持续对话系统，支持丞相、太尉两个 AI 角色跨频道协调工作。

## 核心架构

### 三层架构设计

```
┌─────────────────────────────────────────┐
│           Discord 服务器                 │
│  ┌─────────┬─────────┬─────────┐       │
│  │ 金銮殿  │  内阁   │  兵部   │       │
│  └────┬────┴────┬────┴────┬────┘       │
│       │         │         │            │
│       └─────────┴─────────┘            │
│                 │                       │
│       ┌─────────┴─────────┐            │
│       │   Hub Bot (监听)   │  ← 监听层 │
│       │   使用 Hub Token   │            │
│       └─────────┬─────────┘            │
│                 │                       │
│       ┌─────────┴─────────┐            │
│       │   Message Bus      │  ← 逻辑层 │
│       │   (消息分发/过滤)   │            │
│       └─────────┬─────────┘            │
│                 │                       │
│       ┌─────────┴─────────┐            │
│       ▼                   ▼            │
│   丞相 Bot              太尉 Bot       │
│   (丞相 Token)          (太尉 Token)   │  ← 执行层
└─────────────────────────────────────────┘
```

### 架构说明

| 层级 | 组件 | Token | 职责 |
|------|------|-------|------|
| **监听层** | Hub Bot | Hub Token | 监听所有 3 个频道的消息 |
| **逻辑层** | Message Bus | 无 | 消息分发、上下文过滤、跨频道协调 |
| **执行层** | 丞相 Bot | 丞相 Token | 在金銮殿、内阁发送消息 |
| **执行层** | 太尉 Bot | 太尉 Token | 在金銮殿、内阁、兵部发送消息 |

## 频道配置

```python
CHANNEL_CONFIG = {
    "金銮殿": {
        "channel_id": "1477312823817277681",
        "bots": ["chengxiang", "taiwei"]
    },
    "内阁": {
        "channel_id": "1477312823817277682",
        "bots": ["chengxiang", "taiwei"]
    },
    "兵部": {
        "channel_id": "1477312823817277683",
        "bots": ["taiwei"]
    }
}
```

## 核心组件

### 1. Hub Listener（监听层）

```python
class HubListener:
    """Hub Bot - 使用 Hub Token 监听所有频道"""
    
    def __init__(self, token: str, on_message: Callable):
        self.token = token
        self.on_message = on_message
        self.client = discord.Client(intents=discord.Intents.all())
        
        @self.client.event
        async def on_message(message):
            if message.author.id == self.client.user.id:
                return
            await self.on_message(message)
    
    async def start(self):
        await self.client.start(self.token)
```

### 2. Message Bus（逻辑层）

```python
class MessageBus:
    """消息总线 - 分发消息、管理上下文、协调跨频道任务"""
    
    def __init__(self, role_bots: dict[str, RoleBot]):
        self.role_bots = role_bots
        self.message_history: list[UnifiedMessage] = []
        self.active_tasks: dict[str, CrossChannelTask] = {}
    
    async def publish(self, message: UnifiedMessage):
        """发布消息到总线"""
        self.message_history.append(message)
        
        # 检查是否触发跨频道任务
        task = self.parse_cross_channel_task(message)
        if task:
            self.active_tasks[task.task_id] = task
            for bot_id in task.target_bots:
                await self.role_bots[bot_id].handle_task(task)
        
        # 分发给相关 Bot
        for bot_id, bot in self.role_bots.items():
            if self.should_deliver(bot_id, message):
                await bot.handle_message(message)
    
    def should_deliver(self, bot_id: str, message: UnifiedMessage) -> bool:
        """判断消息是否投递给该 Bot"""
        if bot_id in message.mentions:
            return True
        channel_bots = CHANNEL_CONFIG.get(message.channel_id, [])
        return bot_id in channel_bots
    
    def parse_cross_channel_task(self, message: UnifiedMessage) -> CrossChannelTask | None:
        """解析跨频道指令"""
        content = message.content.lower()
        if "@" in message.content and any(k in content for k in ["去", "到", "在"]):
            target_channel = self.extract_channel(content)
            if target_channel and message.mentions:
                return CrossChannelTask(
                    task_id=str(uuid.uuid4()),
                    source_channel=message.channel_id,
                    target_channel=target_channel,
                    target_bots=message.mentions,
                    instruction=message.content,
                    status="pending"
                )
        return None
```

### 3. Role Bot（执行层）

```python
class RoleBot:
    """角色 Bot - 处理消息、管理状态、生成回复"""
    
    def __init__(self, bot_id: str, token: str, persona: BotPersona):
        self.bot_id = bot_id
        self.token = token
        self.persona = persona
        self.client = discord.Client(intents=discord.Intents.default())
        self.state = BotState.IDLE
        self.context: list[UnifiedMessage] = []
        self.current_task: CrossChannelTask | None = None
    
    async def handle_message(self, message: UnifiedMessage):
        """处理消息"""
        # 更新上下文（仅相关消息）
        if self.is_relevant(message):
            self.context.append(message)
            self.context = self.context[-15:]  # 保留最近15条
        
        # 跨频道任务中的消息处理
        if self.state == BotState.DISCUSSING:
            self.check_conclusion(message)
        
        # 生成响应
        if self.should_respond(message):
            response = await self.generate_response(message)
            await self.send_message(message.channel_id, response)
    
    async def handle_task(self, task: CrossChannelTask):
        """处理跨频道任务"""
        self.state = BotState.DISCUSSING
        self.current_task = task
        
        # 在源频道确认
        await self.send_message(
            task.source_channel,
            f"领旨，即刻去内阁商议。"
        )
        
        # 在目标频道开始
        await self.send_message(
            task.target_channel,
            f"奉陛下旨意，来此商议：{task.instruction}"
        )
    
    def is_relevant(self, message: UnifiedMessage) -> bool:
        """判断消息是否相关"""
        return (
            self.bot_id in message.mentions or
            message.author_id == self.client.user.id or
            self.is_same_topic(message)
        )
    
    async def generate_response(self, message: UnifiedMessage) -> str:
        """生成响应"""
        context = "\n".join([f"{m.author_name}: {m.content}" for m in self.context[-10:]])
        
        prompt = f"""你是{self.persona.name}，{self.persona.description}

相关对话：
{context}

{message.author_name}：{message.content}

请回复："""
        
        # 调用 AI
        client = create_provider("kimi", api_key=self.persona.api_key)
        from ai_toolbox.providers import ChatMessage
        messages = [
            ChatMessage(role="system", content=self.persona.system_prompt),
            ChatMessage(role="user", content=prompt)
        ]
        response = await client.chat(messages)
        return response.content
    
    async def send_message(self, channel_id: str, content: str):
        """发送消息"""
        channel = self.client.get_channel(int(channel_id))
        if channel:
            await channel.send(content)
    
    def check_conclusion(self, message: UnifiedMessage):
        """检查是否形成结论"""
        # 触发条件：讨论5轮以上，或被@且含"结论"关键词
        if len(self.context) >= 10 or (self.bot_id in message.mentions and "结论" in message.content):
            asyncio.create_task(self.form_conclusion())
    
    async def form_conclusion(self):
        """形成结论并汇报"""
        self.state = BotState.REPORTING
        
        # 生成结论
        discussion = "\n".join([f"{m.author_name}: {m.content}" for m in self.context[-20:]])
        prompt = f"基于以下讨论，形成简洁结论：\n{discussion}\n\n结论："
        
        client = create_provider("kimi", api_key=self.persona.api_key)
        from ai_toolbox.providers import ChatMessage
        response = await client.chat([ChatMessage(role="user", content=prompt)])
        conclusion = response.content
        
        # 返回源频道汇报
        await self.send_message(
            self.current_task.source_channel,
            f"启禀陛下，臣等已在内阁商议完毕。\n\n结论：{conclusion}"
        )
        
        # 重置状态
        self.state = BotState.IDLE
        self.current_task = None
        self.context = []
```

### 4. 数据结构

```python
@dataclass
class UnifiedMessage:
    """统一消息格式"""
    id: str
    author_id: str
    author_name: str
    content: str
    channel_id: str
    timestamp: datetime
    mentions: list[str]

@dataclass
class CrossChannelTask:
    """跨频道任务"""
    task_id: str
    source_channel: str
    target_channel: str
    target_bots: list[str]
    instruction: str
    status: str

class BotState:
    """Bot 状态"""
    IDLE = "idle"
    DISCUSSING = "discussing"
    REPORTING = "reporting"

@dataclass
class BotPersona:
    """Bot 角色配置"""
    name: str
    description: str
    system_prompt: str
    api_key: str
```

## 跨频道协调流程

### 场景示例

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
[14:05] 太尉: 可。

[14:06] 丞相: 商议已定，即刻回禀陛下。

=== 金銮殿频道 ===
[14:07] 丞相: 启禀陛下，臣等已在内阁商议完毕。
         结论：加强边境巡逻，增派三千精兵驻守。
```

### 状态流转

```
IDLE → DISCUSSING: 收到跨频道指令
DISCUSSING → REPORTING: 形成结论
REPORTING → IDLE: 汇报完成
```

## 启动代码

```python
async def main():
    # 初始化角色 Bot
    chengxiang = RoleBot(
        bot_id="chengxiang",
        token=os.getenv("CHENGXIANG_BOT_TOKEN"),
        persona=BotPersona(
            name="丞相",
            description="三公之首，统筹决策",
            system_prompt="你是赛博王朝的丞相...",
            api_key=os.getenv("KIMI_API_KEY")
        )
    )
    
    taiwei = RoleBot(
        bot_id="taiwei",
        token=os.getenv("TAIWEI_BOT_TOKEN"),
        persona=BotPersona(
            name="太尉",
            description="三公之一，安全执行",
            system_prompt="你是赛博王朝的太尉...",
            api_key=os.getenv("KIMI_API_KEY")
        )
    )
    
    # 初始化消息总线
    role_bots = {"chengxiang": chengxiang, "taiwei": taiwei}
    bus = MessageBus(role_bots)
    
    # 初始化 Hub 监听
    hub = HubListener(
        token=os.getenv("HUB_BOT_TOKEN"),
        on_message=lambda m: bus.publish(to_unified(m))
    )
    
    # 启动
    await hub.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## 实施计划

| 阶段 | 内容 | 时间 |
|------|------|------|
| Phase 1 | Hub Listener + 频道监听 | 1天 |
| Phase 2 | Message Bus + 消息分发 | 1天 |
| Phase 3 | Role Bot + 上下文过滤 | 1天 |
| Phase 4 | 跨频道协调 + 状态机 | 2天 |
| **总计** | | **5天** |

## 环境变量

```bash
# Hub Bot Token（监听用）
export HUB_BOT_TOKEN="xxx"

# 丞相 Bot Token（发送用）
export CHENGXIANG_BOT_TOKEN="xxx"

# 太尉 Bot Token（发送用）
export TAIWEI_BOT_TOKEN="xxx"

# AI API Key
export KIMI_API_KEY="xxx"
```

---

*最终设计方案 - 整合 V2.1~V2.4*