# 多 Bot 持续对话 - 方案 V2.4（Hub 作为消息总线载体）

## 关键架构澄清

### 消息总线需要 Bot Token

**问题**: Message Bus 监听所有频道消息是否需要 Bot Token？

**答案**: **需要**。在 Discord 中，要监听频道消息，必须：
1. 连接到 Discord Gateway
2. 使用 Bot Token 认证
3. 拥有频道的读取权限

### 解决方案：Hub Bot 作为总线载体

```
架构：
┌─────────────────────────────────────────┐
│           Discord 服务器                 │
│  ┌─────────┬─────────┬─────────┐       │
│  │ 金銮殿  │  内阁   │  兵部   │       │
│  └────┬────┴────┬────┴────┬────┘       │
│       │         │         │            │
│       └─────────┴─────────┘            │
│                 │                       │
│       ┌─────────┴─────────┐            │
│       │   Hub Bot (监听)   │            │
│       │   使用 Hub Token   │            │
│       └─────────┬─────────┘            │
│                 │                       │
│       ┌─────────┼─────────┐            │
│       ▼         ▼         ▼            │
│   丞相Bot    太尉Bot              │
│   (接收)     (接收)              │
│   (发送)     (发送)              │
└─────────────────────────────────────────┘
```

## 架构设计

### 1. 三层架构

```python
class MultiBotSystem:
    """多 Bot 系统 - 三层架构"""
    
    def __init__(self):
        # 第一层：Hub Bot（监听层）
        self.hub_listener = HubListener(
            token=HUB_BOT_TOKEN,  # 赛博王朝 Hub Token
            on_message=self.on_discord_message
        )
        
        # 第二层：消息总线（逻辑层）
        self.message_bus = MessageBus()
        
        # 第三层：角色 Bot（执行层）
        self.role_bots: dict[str, RoleBot] = {
            "chengxiang": RoleBot(
                token=CHENGXIANG_BOT_TOKEN,
                persona=chengxiang_persona
            ),
            "taiwei": RoleBot(
                token=TAIWEI_BOT_TOKEN,
                persona=taiwei_persona
            )
        }
    
    async def on_discord_message(self, message: discord.Message):
        """Hub Bot 收到消息时的回调"""
        # 转换为统一消息格式
        unified = self.to_unified(message)
        
        # 提交到消息总线
        await self.message_bus.publish(unified)
    
    async def start(self):
        """启动系统"""
        # 1. 启动 Hub Bot 监听
        await self.hub_listener.start()
        
        # 2. 启动角色 Bot（仅连接，不监听）
        for bot in self.role_bots.values():
            await bot.connect()
```

### 2. Hub Listener（监听层）

```python
class HubListener:
    """Hub Bot - 负责监听所有频道"""
    
    def __init__(self, token: str, on_message: Callable):
        self.token = token
        self.on_message = on_message
        self.client = discord.Client(intents=discord.Intents.all())
        
        @self.client.event
        async def on_message(message):
            # 忽略自己
            if message.author.id == self.client.user.id:
                return
            
            # 转发到总线
            await self.on_message(message)
    
    async def start(self):
        """启动监听"""
        await self.client.start(self.token)
```

### 3. 角色 Bot（执行层）

```python
class RoleBot:
    """角色 Bot - 负责发送消息和处理逻辑"""
    
    def __init__(self, token: str, persona: BotPersona):
        self.token = token
        self.persona = persona
        self.client = discord.Client(intents=discord.Intents.default())
        self.connected = False
    
    async def connect(self):
        """连接到 Discord（仅用于发送）"""
        # 使用轻量级连接，不需要监听所有消息
        await self.client.login(self.token)
        self.connected = True
    
    async def send_message(self, channel_id: str, content: str):
        """发送消息到指定频道"""
        if not self.connected:
            await self.connect()
        
        channel = self.client.get_channel(int(channel_id))
        if channel:
            await channel.send(content)
```

### 4. 消息总线（逻辑层）

```python
class MessageBus:
    """消息总线 - 纯逻辑层，不直接连接 Discord"""
    
    def __init__(self, role_bots: dict[str, RoleBot]):
        self.role_bots = role_bots
        self.subscribers: list[Callable] = []
        self.message_history: list[UnifiedMessage] = []
    
    async def publish(self, message: UnifiedMessage):
        """发布消息到总线"""
        # 保存历史
        self.message_history.append(message)
        
        # 分发给相关 Bot
        for bot_id, bot in self.role_bots.items():
            if self.should_deliver(bot_id, message):
                await bot.handle_message(message)
    
    def should_deliver(self, bot_id: str, message: UnifiedMessage) -> bool:
        """判断消息是否应该投递给该 Bot"""
        # 1. 被 @ 时投递
        if bot_id in message.mentions:
            return True
        
        # 2. 同一频道的消息
        channel_bots = CHANNEL_MAP.get(message.channel_id, [])
        if bot_id in channel_bots:
            return True
        
        return False
```

## Token 使用策略

| Token | 角色 | 用途 | 频道权限 |
|-------|------|------|----------|
| **Hub** | 监听者 | 监听所有频道消息 | 所有频道读取 |
| **丞相** | 执行者 | 在金銮殿/内阁发送 | 金銮殿、内阁 |
| **太尉** | 执行者 | 在金銮殿/内阁/兵部发送 | 金銮殿、内阁、兵部 |

## 消息流转示例

```
场景：皇帝在金銮殿 @丞相 @太尉

1. 皇帝发送消息
   ↓
2. Hub Bot 监听到消息（使用 Hub Token）
   ↓
3. Hub 将消息提交到 MessageBus
   ↓
4. MessageBus 判断：
   - 丞相被 @，投递给丞相 Bot
   - 太尉被 @，投递给太尉 Bot
   ↓
5. 丞相 Bot 处理（使用丞相 Token 回复）
   太尉 Bot 处理（使用太尉 Token 回复）
```

## 优势

1. **单一监听点**: Hub 负责监听，简化架构
2. **权限分离**: Hub 只有读取权，角色 Bot 只在自己频道发送
3. **可扩展**: 新增 Bot 只需配置频道映射，无需修改 Hub
4. **容错**: Hub 宕机不影响已发送的消息

## 实施调整

### 原方案 vs 新方案

| 项目 | 原方案 | 新方案（V2.4） |
|------|--------|----------------|
| 监听方式 | 每个 Bot 监听自己频道 | Hub 统一监听所有频道 |
| Token 使用 | 3 个 Bot 各自监听 | Hub 监听，2 个 Bot 发送 |
| 架构复杂度 | 中 | 简单 |
| 权限管理 | 复杂 | 清晰 |

### 实施步骤

#### Phase 1: Hub 监听层 (1天)
- [ ] HubListener 实现
- [ ] 连接 3 个频道测试
- [ ] 消息转发到总线

#### Phase 2: 角色 Bot 层 (1天)
- [ ] RoleBot 实现
- [ ] 丞相、太尉连接
- [ ] 发送消息测试

#### Phase 3: 总线整合 (1天)
- [ ] MessageBus 实现
- [ ] 消息分发逻辑
- [ ] 上下文过滤

#### Phase 4: 跨频道协调 (2天)
- [ ] 跨频道指令解析
- [ ] Bot 状态机
- [ ] 完整流程测试

**总计：5天**

---

*方案 V2.4 完成 - 明确 Hub 作为消息总线载体*