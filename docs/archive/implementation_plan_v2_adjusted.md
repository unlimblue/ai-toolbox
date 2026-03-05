# Multi-Bot System V2 实施方案（调整版）

**日期**: 2026-03-05  
**调整内容**: 
1. Bot 自主 @ 格式标准化
2. 详细测试方案

---

## 核心调整点

### 调整 1: Bot 自主 @ 格式标准化

**问题**: Bot 发送的消息中包含 @，需要确保格式正确，能被系统正确识别和路由

**解决方案**:

#### A. @ 格式规范

Bot 发送的消息中，@ 格式必须标准化：

```python
# Bot 内部使用 bot_id，发送时转换为 Discord 格式
class MentionFormatter:
    """格式化 @ 提及，确保可被正确识别"""
    
    @staticmethod
    def format_mention(bot_id: str, config: MultiBotConfig) -> str:
        """
        将 bot_id 转换为 Discord @ 格式
        
        优先级:
        1. 优先使用角色 @ (如果配置了角色ID)
        2. 其次使用用户 @ (如果配置了用户ID)
        """
        # 查找角色ID
        for role_id, mapped_bot_id in config.discord_config.get("role_id_to_bot", {}).items():
            if mapped_bot_id == bot_id:
                return f"<@&{role_id}>"  # 角色 @ 格式
        
        # 查找用户ID
        for user_id, mapped_bot_id in config.discord_config.get("user_id_to_bot", {}).items():
            if mapped_bot_id == bot_id:
                return f"<@{user_id}>"  # 用户 @ 格式
        
        # 兜底：使用名称
        return f"@{bot_id}"
    
    @staticmethod
    def format_mention_by_name(name: str) -> str:
        """直接使用名称 @（不推荐，但兼容）"""
        return f"@{name}"
```

#### B. Bot 发送消息时自动转换

```python
class RoleBot:
    async def send_message(self, channel_id: str, content: str, mentions: list = None):
        """
        发送消息，自动转换 mentions 为 Discord 格式
        
        Args:
            content: 消息内容，可包含 {bot_id} 占位符
            mentions: 需要 @ 的 bot_id 列表
        """
        # 转换 mentions
        if mentions:
            for bot_id in mentions:
                mention_str = MentionFormatter.format_mention(bot_id, self.config)
                # 替换内容中的占位符
                content = content.replace(f"{{{bot_id}}}", mention_str)
        
        # 发送
        channel = self._client.get_channel(int(channel_id))
        if channel:
            sent_message = await channel.send(content)
            
            # 重要：记录这条消息的 mentions，用于后续路由
            await self._record_message_mentions(sent_message.id, mentions)
            
            return sent_message
```

#### C. Hub Listener 增强识别

```python
def discord_message_to_unified(message: discord.Message) -> UnifiedMessage:
    """增强版：识别 Bot 发送的消息中的 mentions"""
    
    mentions = []
    
    # 1. 识别用户 mentions（来自 discord.py）
    for mention in message.mentions:
        discord_id = str(mention.id)
        if discord_id in DISCORD_ID_TO_BOT_ID:
            mentions.append(DISCORD_ID_TO_BOT_ID[discord_id])
    
    # 2. 识别角色 mentions（来自 discord.py）
    for role in message.role_mentions:
        role_id = str(role.id)
        if role_id in ROLE_ID_TO_BOT_ID:
            mentions.append(ROLE_ID_TO_BOT_ID[role_id])
    
    # 3. 【新增】从消息内容中解析 @（备用方案）
    # 当 discord.py 没有识别到时，手动解析
    if not mentions:
        mentions = _parse_mentions_from_content(message.content)
    
    return UnifiedMessage(...)


def _parse_mentions_from_content(content: str) -> list:
    """
    从消息内容中手动解析 @
    
    支持格式：
    - <@user_id> -> 用户 @
    - <@&role_id> -> 角色 @
    - @名称 -> 名称匹配
    """
    mentions = []
    
    # 匹配 <@user_id>
    import re
    user_pattern = r'<@(\d+)>'
    for match in re.finditer(user_pattern, content):
        user_id = match.group(1)
        if user_id in DISCORD_ID_TO_BOT_ID:
            mentions.append(DISCORD_ID_TO_BOT_ID[user_id])
    
    # 匹配 <@&role_id>
    role_pattern = r'<@&(\d+)>'
    for match in re.finditer(role_pattern, content):
        role_id = match.group(1)
        if role_id in ROLE_ID_TO_BOT_ID:
            mentions.append(ROLE_ID_TO_BOT_ID[role_id])
    
    return mentions
```

#### D. 配置扩展

```yaml
# config/multi_bot.yaml

discord:
  # ID 映射
  user_id_to_bot:
    "1477314385713037445": "chengxiang"
    "1478216774171365466": "taiwei"
  
  role_id_to_bot:
    "1477314769764614239": "chengxiang"
    "1478217215936430092": "taiwei"
  
  # 【新增】Bot 主动 @ 时使用的格式偏好
  mention_format_preference: "role"  # "role" 或 "user"
  
  # 【新增】Bot 显示名称映射（用于内容中的 @名称）
  bot_display_names:
    chengxiang: "丞相"
    taiwei: "太尉"
```

---

### 调整 2: 详细测试方案

#### 测试类别 1: @ 格式转换测试

**文件**: `tests/unit/multi_bot/test_mention_format.py`

```python
class TestMentionFormatter:
    """Test mention formatting and parsing"""
    
    def test_format_mention_by_role_id(self):
        """Test formatting mention using role ID"""
        config = Mock()
        config.discord_config = {
            "role_id_to_bot": {
                "1477314769764614239": "chengxiang"
            },
            "user_id_to_bot": {}
        }
        
        result = MentionFormatter.format_mention("chengxiang", config)
        assert result == "<@&1477314769764614239>"
    
    def test_format_mention_by_user_id(self):
        """Test formatting mention using user ID (fallback)"""
        config = Mock()
        config.discord_config = {
            "role_id_to_bot": {},
            "user_id_to_bot": {
                "1477314385713037445": "chengxiang"
            }
        }
        
        result = MentionFormatter.format_mention("chengxiang", config)
        assert result == "<@1477314385713037445>"
    
    def test_format_mention_not_found(self):
        """Test formatting when no ID mapping found"""
        config = Mock()
        config.discord_config = {
            "role_id_to_bot": {},
            "user_id_to_bot": {}
        }
        
        result = MentionFormatter.format_mention("unknown", config)
        assert result == "@unknown"  # 兜底使用名称
    
    def test_parse_mentions_from_content_user(self):
        """Test parsing user mentions from message content"""
        content = "<@1477314385713037445> 你好"
        
        with patch('ai_toolbox.multi_bot.hub_listener.DISORD_ID_TO_BOT_ID', {
            "1477314385713037445": "chengxiang"
        }):
            mentions = _parse_mentions_from_content(content)
        
        assert "chengxiang" in mentions
    
    def test_parse_mentions_from_content_role(self):
        """Test parsing role mentions from message content"""
        content = "<@&1477314769764614239> 你好"
        
        with patch('ai_toolbox.multi_bot.hub_listener.ROLE_ID_TO_BOT_ID', {
            "1477314769764614239": "chengxiang"
        }):
            mentions = _parse_mentions_from_content(content)
        
        assert "chengxiang" in mentions
    
    def test_parse_multiple_mentions(self):
        """Test parsing multiple mentions"""
        content = "<@&1477314769764614239> <@&1478217215936430092> 商议"
        
        with patch('ai_toolbox.multi_bot.hub_listener.ROLE_ID_TO_BOT_ID', {
            "1477314769764614239": "chengxiang",
            "1478217215936430092": "taiwei"
        }):
            mentions = _parse_mentions_from_content(content)
        
        assert "chengxiang" in mentions
        assert "taiwei" in mentions
        assert len(mentions) == 2
```

#### 测试类别 2: Bot 自主 @ 路由测试

**文件**: `tests/integration/test_bot_initiated_mentions.py`

```python
class TestBotInitiatedMentions:
    """Test bot-initiated mentions and routing"""
    
    @pytest.mark.asyncio
    async def test_bot_mention_gets_routed_back(self):
        """
        Test that when Bot A @ Bot B, Bot B receives the message
        
        Flow:
        1. 丞相发送: "@太尉，我们去内阁商议"
        2. 消息通过 Hub 监听
        3. 太尉应该收到这条消息
        """
        bus = MessageBus()
        
        # Create mock bots
        mock_chengxiang = Mock()
        mock_chengxiang.config = Mock()
        mock_chengxiang.config.bot_id = "chengxiang"
        mock_chengxiang.send_message = AsyncMock()
        
        mock_taiwei = Mock()
        mock_taiwei.config = Mock()
        mock_taiwei.config.bot_id = "taiwei"
        mock_taiwei.handle_message = AsyncMock()
        
        bus.register_bot(mock_chengxiang)
        bus.register_bot(mock_taiwei)
        
        # Simulate 丞相发送消息 @太尉
        # 注意：这是从 Discord 收到的消息（丞相发的）
        msg_from_chengxiang = UnifiedMessage(
            id="123",
            author_id="1477314385713037445",  # 丞相用户ID
            author_name="丞相",
            content="<@&1478217215936430092>，我们去内阁商议",  # @太尉
            channel_id="1478759781425745940",
            timestamp=datetime.now(),
            mentions=["taiwei"]  # 应该被识别为 mentions
        )
        
        await bus.publish(msg_from_chengxiang)
        
        # 太尉应该收到
        mock_taiwei.handle_message.assert_called_once()
        
        # 丞相不应该收到（自己发的）
        mock_chengxiang.handle_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cross_channel_bot_discussion(self):
        """
        Test cross-channel discussion between bots
        
        Flow:
        1. 皇帝在金銮殿 @丞相 @太尉
        2. 丞相在内阁 @太尉 "你觉得如何？"
        3. 太尉在内阁回复丞相
        4. 丞相在内阁 @太尉 "那我们就这么定了？"
        5. 丞相回到金銮殿汇报
        """
        bus = MessageBus()
        
        # Track all messages
        messages_sent = []
        
        # Create bots with actual send logic
        class MockBot:
            def __init__(self, bot_id):
                self.bot_id = bot_id
                self.config = Mock()
                self.config.bot_id = bot_id
                self.messages_received = []
            
            async def handle_message(self, msg):
                self.messages_received.append(msg)
                
                # Simulate AI response
                if self.bot_id == "chengxiang" and "taiwei" in msg.mentions:
                    # 丞相 @太尉
                    await self.send_message(
                        msg.channel_id,
                        "<@&1478217215936430092> 你觉得如何？",
                        mentions=["taiwei"]
                    )
            
            async def send_message(self, channel_id, content, mentions=None):
                messages_sent.append({
                    "bot": self.bot_id,
                    "channel": channel_id,
                    "content": content,
                    "mentions": mentions
                })
        
        chengxiang = MockBot("chengxiang")
        taiwei = MockBot("taiwei")
        
        bus.register_bot(chengxiang)
        bus.register_bot(taiwei)
        
        # Step 1: 皇帝 @丞相 @太尉
        emperor_msg = UnifiedMessage(
            id="1",
            author_id="1477269928720466011",
            author_name="皇帝",
            content="去内阁商议",
            channel_id="1478759781425745940",
            mentions=["chengxiang", "taiwei"]
        )
        await bus.publish(emperor_msg)
        
        # 验证两人都收到
        assert len(chengxiang.messages_received) == 1
        assert len(taiwei.messages_received) == 1
    
    @pytest.mark.asyncio
    async def test_bot_self_mention_not_routed(self):
        """Test that bot doesn't receive its own @ messages"""
        bus = MessageBus()
        
        mock_bot = Mock()
        mock_bot.config = Mock()
        mock_bot.config.bot_id = "chengxiang"
        mock_bot.handle_message = AsyncMock()
        
        bus.register_bot(mock_bot)
        
        # Bot 自己发消息（从 Discord 监听）
        own_message = UnifiedMessage(
            id="123",
            author_id="1477314385713037445",  # 丞相自己的ID
            author_name="丞相",
            content="我说点什么",
            channel_id="1478759781425745940",
            mentions=[]
        )
        
        await bus.publish(own_message)
        
        # 自己不应该收到自己的消息
        mock_bot.handle_message.assert_not_called()
```

#### 测试类别 3: AI 决策测试

**文件**: `tests/unit/multi_bot/test_ai_decision.py`

```python
class TestAIDecision:
    """Test AI-driven decision making"""
    
    @pytest.mark.asyncio
    async def test_ai_decides_discuss_action(self):
        """Test AI decides to discuss in another channel"""
        bot = RoleBot(config)
        
        # Mock AI response
        mock_ai_response = {
            "type": "discuss",
            "target_channel": "neige",
            "message": "@太尉，我们去内阁商议此事如何？",
            "mentions": ["taiwei"]
        }
        
        with patch.object(bot, '_call_ai', return_value=mock_ai_response):
            action = await bot._decide_action({
                "message": "去内阁商议",
                "mentions": ["chengxiang", "taiwei"]
            })
        
        assert action["type"] == "discuss"
        assert action["target_channel"] == "neige"
        assert "taiwei" in action["mentions"]
    
    @pytest.mark.asyncio
    async def test_ai_decides_respond_action(self):
        """Test AI decides to respond directly"""
        bot = RoleBot(config)
        
        mock_ai_response = {
            "type": "respond",
            "message": "臣遵旨",
            "mentions": []
        }
        
        with patch.object(bot, '_call_ai', return_value=mock_ai_response):
            action = await bot._decide_action({
                "message": "丞相有何建议？",
                "mentions": ["chengxiang"]
            })
        
        assert action["type"] == "respond"
    
    @pytest.mark.asyncio
    async def test_ai_decides_cross_channel_task(self):
        """Test AI decides to create cross-channel task"""
        bot = RoleBot(config)
        
        mock_ai_response = {
            "type": "cross_channel",
            "source_channel": "jinluan",
            "target_channel": "neige",
            "target_bots": ["chengxiang", "taiwei"],
            "message": "奉旨商议"
        }
        
        with patch.object(bot, '_call_ai', return_value=mock_ai_response):
            action = await bot._decide_action({
                "message": "去内阁商议边防方案",
                "mentions": ["chengxiang", "taiwei"]
            })
        
        assert action["type"] == "cross_channel"
        assert "neige" in action["target_channel"]
```

#### 测试类别 4: 配置加载测试

**文件**: `tests/unit/multi_bot/test_config_loader.py`

```python
class TestMultiBotConfig:
    """Test configuration loading"""
    
    def test_load_organization_config(self):
        """Test loading organization settings"""
        config = MultiBotConfig("test_config.yaml")
        assert config.organization["name"] == "赛博王朝"
    
    def test_load_bot_config(self):
        """Test loading bot configurations"""
        config = MultiBotConfig()
        chengxiang = config.get_bot_config("chengxiang")
        
        assert chengxiang["name"] == "丞相"
        assert chengxiang["title"] == "三公之首"
        assert "persona" in chengxiang
    
    def test_load_channel_config(self):
        """Test loading channel configurations"""
        config = MultiBotConfig()
        jinluan = config.get_channel_config("jinluan")
        
        assert jinluan["id"] == "1478759781425745940"
        assert "chengxiang" in jinluan["allowed_bots"]
    
    def test_resolve_channel_id(self):
        """Test channel name to ID resolution"""
        config = MultiBotConfig()
        
        assert config.resolve_channel_id("jinluan") == "1478759781425745940"
        assert config.resolve_channel_id("neige") == "1477312823817277681"
    
    def test_env_var_override(self):
        """Test environment variable override"""
        os.environ["TEST_API_KEY"] = "overridden_key"
        
        config = MultiBotConfig()
        # Check that ${TEST_API_KEY} is replaced
        bot_config = config.get_bot_config("chengxiang")
        assert "overridden_key" in bot_config.get("api_key", "")
    
    def test_multi_organization_templates(self):
        """Test loading different organization templates"""
        # Load cyber dynasty
        cyber = MultiBotConfig("config/organizations/cyber_dynasty.yaml")
        assert cyber.organization["name"] == "赛博王朝"
        
        # Load corporate board
        corp = MultiBotConfig("config/organizations/corporate_board.yaml")
        assert corp.organization["name"] == "未来科技董事会"
```

---

## 测试覆盖矩阵

| 测试类别 | 测试数量 | 覆盖点 |
|----------|----------|--------|
| @ 格式转换 | 6 | 角色ID、用户ID、兜底、多@ |
| Bot 自主 @ 路由 | 4 | 路由正确性、跨频道、自过滤 |
| AI 决策 | 4 | 讨论、回复、跨频道任务 |
| 配置加载 | 6 | 组织、Bot、频道、环境变量 |
| **总计** | **20** | |

---

*方案已调整，等待陛下指示。*