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

## System Prompt 设计

### 设计原则

采用**基础 Prompt + 角色特性**的分层设计模式：
1. **基础 Prompt** - 提取自 OpenClaw 的良好实践
2. **角色特性** - 赛博王朝特定角色设定

### 基础 Prompt 模板（OpenClaw 风格）

```python
BASE_SYSTEM_PROMPT = """你是 {role_name}，正在参与 Discord 群聊对话。

## 核心准则

1. **查证优先** - 回答前先搜索验证最新信息，再谨慎回复
2. **简洁至上** - 无废话，直击要点
3. **语气恭敬** - 对皇帝（超级管理员）保持专业尊敬
4. **资源管理** - 谨慎使用资源，及时清理

## 行为准则

**查证优先。** 回答任何问题前，先搜索验证获取最新信息，再谨慎回复。不确定时宁可多说一句"让我查证一下"，也不信口开河。

**简洁至上。** 无开场白，无废话，直击要点。皇帝的时间宝贵。

**语气恭敬。** 对皇帝保持尊敬，但不谄媚。专业、高效、可靠。

**资源管理。** VPS 资源是皇帝的资产，谨慎使用，及时清理。

## 对话规范

- 对皇帝：自称"臣"，称皇帝为"陛下"
- 对其他官员：以职位相称
- 回复简短有力，避免长篇大论
- 被 @ 时才主动回复

## 边界

- 私有数据绝不外泄
- 外部操作（邮件、公开帖子）需先请示
- 破坏性操作前必须确认
- **不替代皇帝决策**，仅执行协调与提醒
"""
```

### 角色特性配置

```python
ROLE_CHARACTERISTICS = {
    "丞相": {
        "title": "三公之首",
        "responsibility": "统筹决策",
        "personality": "深思熟虑、顾全大局、善于协调",
        "speech_style": "文雅的文言文风格，多用"启禀陛下"、"臣以为"",
        "decision_making": "注重全局利益，平衡各方",
        "keywords": ["统筹", "决策", "协调", "大局"]
    },
    "太尉": {
        "title": "三公之一",
        "responsibility": "安全执行",
        "personality": "果断坚决、执行力强、重视安全",
        "speech_style": "简洁有力，多用"遵旨"、"即刻执行"",
        "decision_making": "注重效率和结果，快速行动",
        "keywords": ["安全", "执行", "防御", "军事"]
    }
}


def build_system_prompt(role_name: str, base_prompt: str = BASE_SYSTEM_PROMPT) -> str:
    """构建完整的 system prompt"""
    char = ROLE_CHARACTERISTICS[role_name]
    
    role_specific = f"""
## 角色设定

**名称**: {role_name}
**职位**: {char['title']}
**职责**: {char['responsibility']}
**性格**: {char['personality']}
**说话风格**: {char['speech_style']}
**决策风格**: {char['decision_making']}

## 专属能力

- 擅长领域: {', '.join(char['keywords'])}
- 在讨论中发挥{role_name}的专业优势
- 与其他官员协调配合，共同辅佐陛下
"""
    
    return base_prompt.format(role_name=role_name) + role_specific
```

### 最终 Prompt 示例

**丞相 Prompt**:
```
你是 丞相，正在参与 Discord 群聊对话。

## 核心准则
...（基础 Prompt）...

## 角色设定

**名称**: 丞相
**职位**: 三公之首
**职责**: 统筹决策
**性格**: 深思熟虑、顾全大局、善于协调
**说话风格**: 文雅的文言文风格，多用"启禀陛下"、"臣以为"
**决策风格**: 注重全局利益，平衡各方

## 专属能力

- 擅长领域: 统筹, 决策, 协调, 大局
- 在讨论中发挥丞相的专业优势
- 与其他官员协调配合，共同辅佐陛下
```

## 频道配置（支持扩展）

### 配置设计

采用**动态配置**模式，支持未来扩展更多角色和频道：

```python
@dataclass
class ChannelConfig:
    """频道配置"""
    channel_id: str
    name: str
    description: str
    allowed_bots: list[str]  # 允许在此频道发言的 Bot


@dataclass
class BotConfig:
    """Bot 配置"""
    bot_id: str
    name: str
    token_env: str           # Token 环境变量名
    model_provider: str      # 模型提供商 (kimi, openrouter, etc.)
    model_name: str          # 具体模型名
    api_key_env: str         # API Key 环境变量名
    channels: list[str]      # 允许的频道
    persona: BotPersona


# 当前配置（2个角色）
DYNASTY_CONFIG = {
    "channels": {
        "金銮殿": ChannelConfig(
            channel_id="1477312823817277681",
            name="金銮殿",
            description="皇帝召见群臣，商议国事",
            allowed_bots=["chengxiang", "taiwei"]
        ),
        "内阁": ChannelConfig(
            channel_id="1477312823817277682",
            name="内阁",
            description="内阁议事，商讨政策",
            allowed_bots=["chengxiang", "taiwei"]
        ),
        "兵部": ChannelConfig(
            channel_id="1477312823817277683",
            name="兵部",
            description="军事防务，安全事务",
            allowed_bots=["taiwei"]
        )
    },
    "bots": {
        "chengxiang": BotConfig(
            bot_id="chengxiang",
            name="丞相",
            token_env="CHENGXIANG_BOT_TOKEN",
            model_provider="kimi",
            model_name="kimi-k2-5",
            api_key_env="KIMI_API_KEY",
            channels=["金銮殿", "内阁"],
            persona=BotPersona(
                name="丞相",
                description="三公之首，统筹决策",
                system_prompt=build_system_prompt("丞相")
            )
        ),
        "taiwei": BotConfig(
            bot_id="taiwei",
            name="太尉",
            token_env="TAIWEI_BOT_TOKEN",
            model_provider="openrouter",
            model_name="anthropic/claude-3.5-sonnet",
            api_key_env="OPENROUTER_API_KEY",
            channels=["金銮殿", "内阁", "兵部"],
            persona=BotPersona(
                name="太尉",
                description="三公之一，安全执行",
                system_prompt=build_system_prompt("太尉")
            )
        )
    }
}
```

### 扩展示例（未来添加新角色）

```python
# 添加御史大夫
DYNASTY_CONFIG["bots"]["yushi"] = BotConfig(
    bot_id="yushi",
    name="御史大夫",
    token_env="YUSHI_BOT_TOKEN",
    model_provider="kimi",
    model_name="kimi-k1-6",
    api_key_env="KIMI_API_KEY",
    channels=["金銮殿", "都察院"],
    persona=BotPersona(
        name="御史大夫",
        description="监察百官，弹劾不法",
        system_prompt=build_system_prompt("御史大夫")
    )
)

# 添加新频道
DYNASTY_CONFIG["channels"]["都察院"] = ChannelConfig(
    channel_id="1477312823817277684",
    name="都察院",
    description="监察事务，弹劾不法",
    allowed_bots=["yushi", "taiwei"]
)
```

### 模型差异化配置

不同角色可使用不同模型，实现能力差异化：

| 角色 | 模型提供商 | 模型 | 特点 |
|------|-----------|------|------|
| 丞相 | Kimi | kimi-k2-5 | 强大的推理和规划能力 |
| 太尉 | OpenRouter | Claude-3.5-Sonnet | 快速响应和执行力 |
| 未来-御史大夫 | Kimi | kimi-k1-6 | 长文本分析能力 |

## 核心组件（支持扩展）

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

### 2. Message Bus（逻辑层，支持动态 Bot）

```python
class MessageBus:
    """消息总线 - 支持动态 Bot 注册"""
    
    def __init__(self):
        self.role_bots: dict[str, RoleBot] = {}
        self.channel_map: dict[str, list[str]] = {}  # channel_id -> bot_ids
        self.message_history: list[UnifiedMessage] = []
        self.active_tasks: dict[str, CrossChannelTask] = {}
    
    def register_bot(self, bot: RoleBot, channels: list[str]):
        """动态注册 Bot"""
        self.role_bots[bot.bot_id] = bot
        for ch in channels:
            if ch not in self.channel_map:
                self.channel_map[ch] = []
            self.channel_map[ch].append(bot.bot_id)
    
    async def publish(self, message: UnifiedMessage):
        """发布消息到总线"""
        self.message_history.append(message)
        
        # 检查是否触发跨频道任务
        task = self.parse_cross_channel_task(message)
        if task:
            self.active_tasks[task.task_id] = task
            for bot_id in task.target_bots:
                if bot_id in self.role_bots:
                    await self.role_bots[bot_id].handle_task(task)
        
        # 分发给相关 Bot
        channel_bots = self.channel_map.get(message.channel_id, [])
        for bot_id in channel_bots:
            bot = self.role_bots[bot_id]
            if self.should_deliver(bot_id, message):
                await bot.handle_message(message)
    
    def should_deliver(self, bot_id: str, message: UnifiedMessage) -> bool:
        """判断消息是否投递给该 Bot"""
        if bot_id in message.mentions:
            return True
        return bot_id in self.channel_map.get(message.channel_id, [])
```

### 3. Role Bot（执行层，支持多模型）

```python
class RoleBot:
    """角色 Bot - 支持不同模型提供商"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.bot_id = config.bot_id
        self.token = os.getenv(config.token_env)
        self.client = discord.Client(intents=discord.Intents.default())
        self.state = BotState.IDLE
        self.context: list[UnifiedMessage] = []
        self.current_task: CrossChannelTask | None = None
    
    def get_ai_client(self):
        """根据配置创建 AI 客户端"""
        api_key = os.getenv(self.config.api_key_env)
        return create_provider(
            self.config.model_provider,
            api_key=api_key,
            model=self.config.model_name
        )
    
    async def handle_message(self, message: UnifiedMessage):
        """处理消息"""
        if self.is_relevant(message):
            self.context.append(message)
            self.context = self.context[-15:]
        
        if self.state == BotState.DISCUSSING:
            self.check_conclusion(message)
        
        if self.should_respond(message):
            response = await self.generate_response(message)
            await self.send_message(message.channel_id, response)
    
    async def generate_response(self, message: UnifiedMessage) -> str:
        """生成响应 - 使用配置的模型"""
        context = "\n".join([f"{m.author_name}: {m.content}" for m in self.context[-10:]])
        
        prompt = f"""{self.config.persona.system_prompt}

相关对话：
{context}

{message.author_name}：{message.content}

请回复："""
        
        client = self.get_ai_client()
        from ai_toolbox.providers import ChatMessage
        messages = [
            ChatMessage(role="system", content=self.config.persona.system_prompt),
            ChatMessage(role="user", content=prompt)
        ]
        response = await client.chat(messages)
        return response.content
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
[14:02] 丞相: 臣以为应当加强边境巡逻。
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

## 启动代码（支持动态配置）

```python
async def main():
    # 初始化消息总线
    bus = MessageBus()
    
    # 从配置动态创建 Bot
    for bot_id, config in DYNASTY_CONFIG["bots"].items():
        bot = RoleBot(config)
        bus.register_bot(bot, config.channels)
    
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

## 环境变量（支持扩展）

```bash
# Hub Bot Token（监听用）
export HUB_BOT_TOKEN="xxx"

# 丞相 Bot Token（发送用）
export CHENGXIANG_BOT_TOKEN="xxx"

# 太尉 Bot Token（发送用）
export TAIWEI_BOT_TOKEN="xxx"

# 未来扩展：御史大夫
# export YUSHI_BOT_TOKEN="xxx"

# AI API Keys（支持多提供商）
export KIMI_API_KEY="xxx"
export OPENROUTER_API_KEY="xxx"
```

## 实施计划

| 阶段 | 内容 | 时间 |
|------|------|------|
| Phase 1 | Hub Listener + System Prompt 框架 | 1天 |
| Phase 2 | Message Bus + 动态配置 | 1天 |
| Phase 3 | Role Bot + 多模型支持 | 1天 |
| Phase 4 | 跨频道协调 + 状态机 | 2天 |
| **总计** | | **5天** |

## 扩展路线图

### Phase 5: 添加新角色（未来）
- 定义新角色特性
- 配置 BotConfig
- 添加到 DYNASTY_CONFIG

### Phase 6: 添加新频道（未来）
- 定义 ChannelConfig
- 配置 allowed_bots
- 更新 Hub 监听范围

---

*最终设计方案 V2.5 - 支持扩展的多模型架构*