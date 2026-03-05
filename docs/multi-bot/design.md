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

## Token 安全管理

### 安全原则

1. **绝不硬编码**: Token 绝不写入代码或配置文件
2. **环境变量**: 所有 Token 通过环境变量注入
3. **文件隔离**: Token 存储在独立的 secrets 文件，加入 .gitignore
4. **最小权限**: 每个 Bot Token 仅拥有必要频道的权限

### Token 存储方案

```bash
# ~/.openclaw/secrets/cyber_dynasty_tokens.env
# 该文件已添加到 .gitignore，不会提交到 GitHub

# Hub Bot Token（监听所有频道）
HUB_BOT_TOKEN=MTQ3ODIyMjg0OTgwOTU4NDI0OQ.xxxxx.xxxxxxxxxxxxx

# 丞相 Bot Token
CHENGXIANG_BOT_TOKEN=MTQ3NzMxNDM4NTcxMzAzNzQ0NQ.xxxxx.xxxxxxxxxxxxx

# 太尉 Bot Token
TAIWEI_BOT_TOKEN=MTQ3ODIxNjc3NDE3MTM2NTQ2Ng.xxxxx.xxxxxxxxxxxxx

# AI API Key
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 代码中的 Token 使用

```python
import os
from dotenv import load_dotenv

# 加载环境变量（从 secrets 文件）
load_dotenv(os.path.expanduser("~/.openclaw/secrets/cyber_dynasty_tokens.env"))

# 使用环境变量获取 Token
HUB_TOKEN = os.getenv("HUB_BOT_TOKEN")
CHENGXIANG_TOKEN = os.getenv("CHENGXIANG_BOT_TOKEN")
TAIWEI_TOKEN = os.getenv("TAIWEI_BOT_TOKEN")
KIMI_KEY = os.getenv("KIMI_API_KEY")

# 验证 Token 存在
if not HUB_TOKEN:
    raise ValueError("HUB_BOT_TOKEN not set in environment")
```

### 部署时的安全措施

```bash
# 1. 生产环境设置文件权限
chmod 600 ~/.openclaw/secrets/cyber_dynasty_tokens.env

# 2. 使用 systemd 服务时，通过 EnvironmentFile 加载
# /etc/systemd/system/cyber-dynasty.service
[Service]
EnvironmentFile=/root/.openclaw/secrets/cyber_dynasty_tokens.env

# 3. Docker 部署时使用 secrets
# docker-compose.yml
secrets:
  bot_tokens:
    file: ./secrets/cyber_dynasty_tokens.env
```

### Token 泄露应急处理

1. **立即在 Discord Developer Portal 重置 Token**
2. **更新环境变量文件**
3. **重启服务**
4. **检查 GitHub 提交历史，确保无泄露**

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
    model_provider: str      # 模型提供商
    model_name: str          # 具体模型名
    api_key_env: str         # API Key 环境变量名
    channels: list[str]      # 允许的频道
    persona: BotPersona


# 当前配置（2个角色，统一使用 Kimi）
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
            model_provider="kimi",
            model_name="kimi-k2-5",  # 统一使用 Kimi
            api_key_env="KIMI_API_KEY",
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
# 添加御史大夫（同样使用 Kimi）
DYNASTY_CONFIG["bots"]["yushi"] = BotConfig(
    bot_id="yushi",
    name="御史大夫",
    token_env="YUSHI_BOT_TOKEN",
    model_provider="kimi",
    model_name="kimi-k2-5",
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

### 模型配置

| 角色 | 模型提供商 | 模型 | 特点 |
|------|-----------|------|------|
| 丞相 | Kimi | kimi-k2-5 | 强大的推理和规划能力 |
| 太尉 | Kimi | kimi-k2-5 | 强大的推理和规划能力 |
| 未来角色 | Kimi | kimi-k2-5 | 统一使用 Kimi 便于管理 |

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

### 3. Role Bot（执行层）

```python
class RoleBot:
    """角色 Bot"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.bot_id = config.bot_id
        self.token = os.getenv(config.token_env)
        self.client = discord.Client(intents=discord.Intents.default())
        self.state = BotState.IDLE
        self.context: list[UnifiedMessage] = []
        self.current_task: CrossChannelTask | None = None
    
    def get_ai_client(self):
        """创建 AI 客户端"""
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
        """生成响应"""
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

## 测试方案

### 测试原则

1. **分层测试**: 单元测试 → 集成测试 → 端到端测试
2. **模拟优先**: 使用 mock 避免真实 Discord/API 调用
3. **场景覆盖**: 覆盖正常流程和异常边界
4. **自动化**: 所有测试可自动运行

### 1. 单元测试

#### 1.1 Hub Listener 测试

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch

class TestHubListener:
    """Hub Listener 单元测试"""
    
    @pytest.fixture
    def mock_discord_client(self):
        """模拟 Discord 客户端"""
        with patch('discord.Client') as mock:
            yield mock
    
    @pytest.fixture
    def hub_listener(self):
        callback = AsyncMock()
        return HubListener(token="test_token", on_message=callback)
    
    @pytest.mark.asyncio
    async def test_ignore_own_message(self, hub_listener):
        """测试忽略自己的消息"""
        # 模拟自己发送的消息
        own_message = Mock()
        own_message.author.id = hub_listener.client.user.id
        
        # 触发 on_message
        await hub_listener.client.event_handlers['on_message'](own_message)
        
        # 验证回调未被调用
        hub_listener.on_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_forward_other_message(self, hub_listener):
        """测试转发他人消息"""
        # 模拟他人消息
        other_message = Mock()
        other_message.author.id = 12345  # 不同 ID
        other_message.content = "测试消息"
        
        # 触发 on_message
        await hub_listener.client.event_handlers['on_message'](other_message)
        
        # 验证回调被调用
        hub_listener.on_message.assert_called_once()
```

#### 1.2 Message Bus 测试

```python
class TestMessageBus:
    """Message Bus 单元测试"""
    
    @pytest.fixture
    def message_bus(self):
        return MessageBus()
    
    @pytest.fixture
    def mock_bot(self):
        bot = Mock()
        bot.handle_message = AsyncMock()
        bot.handle_task = AsyncMock()
        return bot
    
    def test_register_bot(self, message_bus, mock_bot):
        """测试 Bot 注册"""
        mock_bot.bot_id = "chengxiang"
        message_bus.register_bot(mock_bot, ["金銮殿", "内阁"])
        
        assert "chengxiang" in message_bus.role_bots
        assert "chengxiang" in message_bus.channel_map["金銮殿"]
        assert "chengxiang" in message_bus.channel_map["内阁"]
    
    @pytest.mark.asyncio
    async def test_deliver_to_mentioned_bot(self, message_bus, mock_bot):
        """测试消息投递给被 @ 的 Bot"""
        mock_bot.bot_id = "chengxiang"
        message_bus.register_bot(mock_bot, ["金銮殿"])
        
        message = UnifiedMessage(
            id="1",
            author_id="123",
            author_name="皇帝",
            content="@丞相 测试",
            channel_id="1477312823817277681",
            timestamp=datetime.now(),
            mentions=["chengxiang"]
        )
        
        await message_bus.publish(message)
        
        mock_bot.handle_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cross_channel_task_parsing(self, message_bus):
        """测试跨频道任务解析"""
        message = UnifiedMessage(
            id="1",
            author_id="123",
            author_name="皇帝",
            content="@丞相 @太尉 去内阁商议",
            channel_id="1477312823817277681",
            timestamp=datetime.now(),
            mentions=["chengxiang", "taiwei"]
        )
        
        task = message_bus.parse_cross_channel_task(message)
        
        assert task is not None
        assert task.target_channel == "1477312823817277682"  # 内阁
        assert "chengxiang" in task.target_bots
        assert "taiwei" in task.target_bots
```

#### 1.3 Role Bot 测试

```python
class TestRoleBot:
    """Role Bot 单元测试"""
    
    @pytest.fixture
    def bot_config(self):
        return BotConfig(
            bot_id="chengxiang",
            name="丞相",
            token_env="TEST_TOKEN",
            model_provider="kimi",
            model_name="kimi-k2-5",
            api_key_env="TEST_API_KEY",
            channels=["金銮殿"],
            persona=BotPersona(
                name="丞相",
                description="测试",
                system_prompt="你是丞相"
            )
        )
    
    @pytest.fixture
    def role_bot(self, bot_config):
        with patch.dict(os.environ, {"TEST_TOKEN": "test", "TEST_API_KEY": "test"}):
            return RoleBot(bot_config)
    
    def test_is_relevant_when_mentioned(self, role_bot):
        """测试被 @ 时判定为相关"""
        message = UnifiedMessage(
            id="1",
            author_id="123",
            author_name="皇帝",
            content="@丞相 测试",
            channel_id="1477312823817277681",
            timestamp=datetime.now(),
            mentions=["chengxiang"]
        )
        
        assert role_bot.is_relevant(message) is True
    
    @pytest.mark.asyncio
    async def test_state_transition_to_discussing(self, role_bot):
        """测试状态转换到 DISCUSSING"""
        task = CrossChannelTask(
            task_id="test_task",
            source_channel="金銮殿",
            target_channel="内阁",
            target_bots=["chengxiang"],
            instruction="测试任务",
            status="pending"
        )
        
        with patch.object(role_bot, 'send_message', new=AsyncMock()):
            await role_bot.handle_task(task)
        
        assert role_bot.state == BotState.DISCUSSING
        assert role_bot.current_task == task
```

### 2. 集成测试

#### 2.1 消息流转测试

```python
class TestMessageFlow:
    """消息流转集成测试"""
    
    @pytest.fixture
    async def system(self):
        """初始化完整系统"""
        bus = MessageBus()
        
        # 创建模拟 Bot
        chengxiang = MockRoleBot("chengxiang")
        taiwei = MockRoleBot("taiwei")
        
        bus.register_bot(chengxiang, ["金銮殿", "内阁"])
        bus.register_bot(taiwei, ["金銮殿", "内阁", "兵部"])
        
        yield {
            "bus": bus,
            "chengxiang": chengxiang,
            "taiwei": taiwei
        }
    
    @pytest.mark.asyncio
    async def test_cross_channel_flow(self, system):
        """测试跨频道完整流程"""
        bus = system["bus"]
        chengxiang = system["chengxiang"]
        taiwei = system["taiwei"]
        
        # 1. 皇帝在金銮殿发起跨频道任务
        emperor_message = UnifiedMessage(
            id="1",
            author_id="1477269928720466011",
            author_name="皇帝",
            content="@丞相 @太尉 去内阁商议方案",
            channel_id="1477312823817277681",
            timestamp=datetime.now(),
            mentions=["chengxiang", "taiwei"]
        )
        
        await bus.publish(emperor_message)
        
        # 2. 验证两个 Bot 都收到任务
        assert chengxiang.handle_task.called
        assert taiwei.handle_task.called
        
        # 3. 验证 Bot 切换到 DISCUSSING 状态
        assert chengxiang.state == BotState.DISCUSSING
        assert taiwei.state == BotState.DISCUSSING
```

#### 2.2 上下文过滤测试

```python
class TestContextFilter:
    """上下文过滤集成测试"""
    
    @pytest.mark.asyncio
    async def test_relevant_message_filtering(self):
        """测试相关消息过滤"""
        bot = MockRoleBot("chengxiang")
        
        # 添加一些消息到上下文
        relevant_messages = [
            UnifiedMessage(id="1", mentions=["chengxiang"], ...),  # 被 @
            UnifiedMessage(id="2", author_id="chengxiang", ...),   # 自己发的
        ]
        
        irrelevant_messages = [
            UnifiedMessage(id="3", mentions=["taiwei"], ...),      # 没 @ 我
            UnifiedMessage(id="4", author_id="hub", ...),          # Hub 的消息
        ]
        
        for msg in relevant_messages + irrelevant_messages:
            if bot.is_relevant(msg):
                bot.context.append(msg)
        
        # 验证只有相关消息被保存
        assert len(bot.context) == 2
        assert all(msg.id in ["1", "2"] for msg in bot.context)
```

### 3. 端到端测试

#### 3.1 完整场景模拟

```python
class TestEndToEnd:
    """端到端测试 - 使用真实 Discord 客户端模拟"""
    
    @pytest.fixture(scope="module")
    def test_env(self):
        """设置测试环境"""
        # 使用测试服务器和测试 Token
        os.environ["HUB_BOT_TOKEN"] = "TEST_HUB_TOKEN"
        os.environ["CHENGXIANG_BOT_TOKEN"] = "TEST_CHENGXIANG_TOKEN"
        os.environ["TAIWEI_BOT_TOKEN"] = "TEST_TAIWEI_TOKEN"
        os.environ["KIMI_API_KEY"] = "TEST_KIMI_KEY"
        
        # 使用测试频道 ID
        TEST_CHANNELS = {
            "金銮殿": "9999999999999999991",
            "内阁": "9999999999999999992",
            "兵部": "9999999999999999993"
        }
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("RUN_E2E"), reason="需要 RUN_E2E 环境变量")
    async def test_full_conversation_flow(self, test_env):
        """测试完整对话流程"""
        # 启动完整系统
        system = await start_test_system()
        
        try:
            # 1. 模拟皇帝发送跨频道指令
            await simulate_message(
                channel="金銮殿",
                author="皇帝",
                content="@丞相 @太尉 去内阁商议边防方案"
            )
            
            # 2. 等待 Bot 响应
            await asyncio.sleep(2)
            
            # 3. 验证丞相和太尉在金銮殿确认
            messages = await get_channel_messages("金銮殿")
            assert any("领旨" in m.content for m in messages)
            assert any("遵旨" in m.content for m in messages)
            
            # 4. 验证 Bot 在内阁开始讨论
            await simulate_message(
                channel="内阁",
                author="丞相",
                content="奉陛下旨意"
            )
            
            await asyncio.sleep(2)
            
            messages = await get_channel_messages("内阁")
            assert any("奉陛下旨意" in m.content for m in messages)
            
        finally:
            await system.shutdown()
```

### 4. 性能测试

```python
class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_message_throughput(self):
        """测试消息吞吐量"""
        bus = MessageBus()
        
        # 注册模拟 Bot
        for i in range(10):
            bot = MockRoleBot(f"bot_{i}")
            bus.register_bot(bot, ["test_channel"])
        
        # 发送 1000 条消息
        start_time = time.time()
        
        tasks = []
        for i in range(1000):
            msg = UnifiedMessage(
                id=str(i),
                author_id="123",
                author_name="test",
                content=f"消息 {i}",
                channel_id="test_channel",
                timestamp=datetime.now(),
                mentions=[]
            )
            tasks.append(bus.publish(msg))
        
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        throughput = 1000 / elapsed
        
        print(f"吞吐量: {throughput:.2f} 消息/秒")
        assert throughput > 100  # 至少 100 msg/s
    
    @pytest.mark.asyncio
    async def test_context_memory_usage(self):
        """测试上下文内存使用"""
        bot = MockRoleBot("test")
        
        # 添加大量消息到上下文
        for i in range(10000):
            msg = UnifiedMessage(
                id=str(i),
                author_id="123",
                author_name="test",
                content="x" * 1000,  # 1KB 内容
                channel_id="test",
                timestamp=datetime.now(),
                mentions=["test"]
            )
            bot.context.append(msg)
            
            # 触发长度限制
            if len(bot.context) > 15:
                bot.context = bot.context[-15:]
        
        # 验证内存使用合理
        import sys
        context_size = sys.getsizeof(bot.context)
        for msg in bot.context:
            context_size += sys.getsizeof(msg)
        
        # 15 条消息应该小于 50KB
        assert context_size < 50 * 1024
```

### 5. 测试覆盖要求

| 组件 | 单元测试 | 集成测试 | 端到端 | 覆盖率目标 |
|------|----------|----------|--------|-----------|
| Hub Listener | ✅ | ✅ | ✅ | 90% |
| Message Bus | ✅ | ✅ | ✅ | 90% |
| Role Bot | ✅ | ✅ | ✅ | 85% |
| Context Filter | ✅ | ✅ | - | 85% |
| Cross Channel | - | ✅ | ✅ | 80% |

### 6. 测试执行命令

```bash
# 运行所有测试
pytest tests/ -v

# 仅运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行端到端测试（需要真实环境）
RUN_E2E=1 pytest tests/e2e/ -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 性能测试
pytest tests/performance/ -v
```

## 启动代码（支持动态配置）

```python
import os
from dotenv import load_dotenv

async def main():
    # 从安全位置加载环境变量
    env_path = os.path.expanduser("~/.openclaw/secrets/cyber_dynasty_tokens.env")
    load_dotenv(env_path)
    
    # 验证必要的环境变量
    required_vars = [
        "HUB_BOT_TOKEN",
        "CHENGXIANG_BOT_TOKEN",
        "TAIWEI_BOT_TOKEN",
        "KIMI_API_KEY"
    ]
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing required environment variable: {var}")
    
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
# Token 文件位置：~/.openclaw/secrets/cyber_dynasty_tokens.env
# 该文件已添加到 .gitignore

# Hub Bot Token（监听用）
HUB_BOT_TOKEN=xxx

# 丞相 Bot Token（发送用）
CHENGXIANG_BOT_TOKEN=xxx

# 太尉 Bot Token（发送用）
TAIWEI_BOT_TOKEN=xxx

# AI API Key（统一使用 Kimi）
KIMI_API_KEY=xxx
```

## 实施计划

| 阶段 | 内容 | 时间 | 测试要求 |
|------|------|------|----------|
| Phase 1 | Hub Listener + System Prompt 框架 | 1天 | 单元测试覆盖 90% |
| Phase 2 | Message Bus + 动态配置 | 1天 | 集成测试通过 |
| Phase 3 | Role Bot + 上下文过滤 | 1天 | 单元测试覆盖 85% |
| Phase 4 | 跨频道协调 + 状态机 | 2天 | 端到端测试通过 |
| **总计** | | **5天** | 整体覆盖率 > 85% |

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

*最终设计方案 V2.6 - 统一 Kimi，全面测试，Token 安全*