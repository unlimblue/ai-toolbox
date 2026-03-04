"""Unit tests for Multi-Bot System."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_toolbox.multi_bot.models import (
    UnifiedMessage,
    CrossChannelTask,
    BotState,
    BotPersona,
    ChannelConfig,
    BotConfig,
)
from ai_toolbox.multi_bot.config import (
    build_system_prompt,
    ROLE_CHARACTERISTICS,
    BASE_SYSTEM_PROMPT,
    DYNASTY_CONFIG,
)


class TestModels:
    """Test data models."""
    
    def test_unified_message_creation(self):
        """Test UnifiedMessage creation."""
        msg = UnifiedMessage(
            id="123",
            author_id="456",
            author_name="TestUser",
            content="Hello",
            channel_id="789",
            timestamp=datetime.now(),
            mentions=["bot1"]
        )
        
        assert msg.id == "123"
        assert msg.author_name == "TestUser"
        assert msg.content == "Hello"
        assert "bot1" in msg.mentions
    
    def test_cross_channel_task_creation(self):
        """Test CrossChannelTask creation."""
        task = CrossChannelTask(
            task_id="task-123",
            source_channel="chan-1",
            target_channel="chan-2",
            target_bots=["bot1", "bot2"],
            instruction="Test instruction"
        )
        
        assert task.task_id == "task-123"
        assert task.status == "pending"
        assert len(task.target_bots) == 2
    
    def test_bot_persona_creation(self):
        """Test BotPersona creation."""
        persona = BotPersona(
            name="丞相",
            description="三公之首",
            system_prompt="你是丞相"
        )
        
        assert persona.name == "丞相"
        assert "三公之首" in persona.description


class TestConfig:
    """Test configuration."""
    
    def test_base_system_prompt(self):
        """Test base system prompt exists and is not empty."""
        assert BASE_SYSTEM_PROMPT
        assert "核心准则" in BASE_SYSTEM_PROMPT
        assert "查证优先" in BASE_SYSTEM_PROMPT
    
    def test_role_characteristics(self):
        """Test role characteristics are defined."""
        assert "丞相" in ROLE_CHARACTERISTICS
        assert "太尉" in ROLE_CHARACTERISTICS
        
        chengxiang = ROLE_CHARACTERISTICS["丞相"]
        assert chengxiang["title"] == "三公之首"
        assert "统筹" in chengxiang["keywords"]
    
    def test_build_system_prompt_chengxiang(self):
        """Test building system prompt for 丞相."""
        prompt = build_system_prompt("丞相")
        
        assert "丞相" in prompt
        assert "三公之首" in prompt
        assert "核心准则" in prompt
        assert "启禀陛下" in prompt
    
    def test_build_system_prompt_taiwei(self):
        """Test building system prompt for 太尉."""
        prompt = build_system_prompt("太尉")
        
        assert "太尉" in prompt
        assert "三公之一" in prompt
        assert "遵旨" in prompt
    
    def test_build_system_prompt_unknown_role(self):
        """Test building prompt for unknown role raises error."""
        with pytest.raises(ValueError, match="Unknown role"):
            build_system_prompt("unknown_role")
    
    def test_dynasty_config_channels(self):
        """Test DynastyConfig has channel configs."""
        assert "金銮殿" in DYNASTY_CONFIG.channels
        assert "内阁" in DYNASTY_CONFIG.channels
        assert "兵部" in DYNASTY_CONFIG.channels
        
        jinluan = DYNASTY_CONFIG.channels["金銮殿"]
        assert jinluan.channel_id == "1477312823817277681"
        assert "chengxiang" in jinluan.allowed_bots
        assert "taiwei" in jinluan.allowed_bots
    
    def test_dynasty_config_bots(self):
        """Test DynastyConfig has bot configs."""
        assert "chengxiang" in DYNASTY_CONFIG.bots
        assert "taiwei" in DYNASTY_CONFIG.bots
        
        chengxiang = DYNASTY_CONFIG.bots["chengxiang"]
        assert chengxiang.name == "丞相"
        assert chengxiang.model_provider == "kimi"
    
    def test_get_channel_by_id(self):
        """Test getting channel by ID."""
        channel = DYNASTY_CONFIG.get_channel_by_id("1477312823817277681")
        assert channel.name == "金銮殿"
    
    def test_get_channel_by_id_invalid(self):
        """Test getting invalid channel raises error."""
        with pytest.raises(ValueError, match="Unknown channel ID"):
            DYNASTY_CONFIG.get_channel_by_id("invalid-id")
    
    def test_get_bot_config(self):
        """Test getting bot config."""
        config = DYNASTY_CONFIG.get_bot_config("chengxiang")
        assert config.bot_id == "chengxiang"
    
    def test_get_allowed_bots_for_channel(self):
        """Test getting allowed bots for channel."""
        bots = DYNASTY_CONFIG.get_allowed_bots_for_channel("1477312823817277681")
        assert "chengxiang" in bots
        assert "taiwei" in bots


class TestMessageBus:
    """Test MessageBus functionality."""
    
    @pytest.fixture
    def message_bus(self):
        """Create MessageBus instance."""
        from ai_toolbox.multi_bot.message_bus import MessageBus
        return MessageBus()
    
    @pytest.fixture
    def mock_bot(self):
        """Create mock RoleBot."""
        bot = Mock()
        bot.config = Mock()
        bot.config.bot_id = "test_bot"
        bot.config.channels = ["金銮殿"]
        bot.handle_message = AsyncMock()
        bot.handle_task = AsyncMock()
        return bot
    
    def test_register_bot(self, message_bus, mock_bot):
        """Test registering a bot."""
        message_bus.register_bot(mock_bot)
        
        assert "test_bot" in message_bus.role_bots
    
    def test_unregister_bot(self, message_bus, mock_bot):
        """Test unregistering a bot."""
        message_bus.register_bot(mock_bot)
        message_bus.unregister_bot("test_bot")
        
        assert "test_bot" not in message_bus.role_bots
    
    @pytest.mark.asyncio
    async def test_publish_message(self, message_bus, mock_bot):
        """Test publishing a message."""
        message_bus.register_bot(mock_bot)
        
        msg = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="User",
            content="Hello",
            channel_id="1477312823817277681",
            timestamp=datetime.now(),
            mentions=["test_bot"]
        )
        
        await message_bus.publish(msg)
        
        # Message should be in history
        assert len(message_bus.message_history) == 1
        
        # Bot should have been called
        mock_bot.handle_message.assert_called_once()
    
    def test_subscribe(self, message_bus):
        """Test subscribing to messages."""
        callback = Mock()
        message_bus.subscribe(callback)
        
        assert callback in message_bus._subscribers
    
    @pytest.mark.asyncio
    async def test_subscriber_called(self, message_bus):
        """Test subscriber is called on publish."""
        callback = AsyncMock()
        message_bus.subscribe(callback)
        
        msg = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="User",
            content="Hello",
            channel_id="chan1",
            timestamp=datetime.now(),
            mentions=[]
        )
        
        await message_bus.publish(msg)
        
        callback.assert_called_once_with(msg)
    
    def test_get_message_history(self, message_bus):
        """Test getting message history."""
        # Add some messages
        for i in range(5):
            msg = UnifiedMessage(
                id=str(i),
                author_id="user1",
                author_name="User",
                content=f"Message {i}",
                channel_id="chan1",
                timestamp=datetime.now(),
                mentions=[]
            )
            message_bus.message_history.append(msg)
        
        history = message_bus.get_message_history(limit=3)
        assert len(history) == 3
        assert history[-1].content == "Message 4"


class TestRoleBot:
    """Test RoleBot functionality."""
    
    @pytest.fixture
    def bot_config(self):
        """Create bot config."""
        return BotConfig(
            bot_id="test_bot",
            name="Test Bot",
            token_env="TEST_TOKEN",
            model_provider="kimi",
            model_name="kimi-k2-5",
            api_key_env="TEST_API_KEY",
            channels=["金銮殿"],
            persona=BotPersona(
                name="Test",
                description="Test bot",
                system_prompt="You are a test bot"
            )
        )
    
    @pytest.fixture
    def role_bot(self, bot_config):
        """Create RoleBot instance with mocked token."""
        with patch.dict('os.environ', {'TEST_TOKEN': 'test_token_123'}):
            from ai_toolbox.multi_bot.role_bot import RoleBot
            return RoleBot(bot_config)
    
    def test_initial_state(self, role_bot):
        """Test initial bot state."""
        assert role_bot.state == BotState.IDLE
        assert len(role_bot.context) == 0
        assert role_bot.current_task is None
    
    def test_is_relevant_when_mentioned(self, role_bot):
        """Test message is relevant when bot is mentioned."""
        msg = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="User",
            content="@test_bot Hello",
            channel_id="chan1",
            timestamp=datetime.now(),
            mentions=["test_bot"]
        )
        
        assert role_bot._is_relevant(msg) is True
    
    def test_is_relevant_own_message(self, role_bot):
        """Test own message is relevant."""
        msg = UnifiedMessage(
            id="1",
            author_id="test_bot",
            author_name="Test Bot",
            content="Hello",
            channel_id="chan1",
            timestamp=datetime.now(),
            mentions=[]
        )
        
        assert role_bot._is_relevant(msg) is True
    
    def test_should_respond_when_mentioned(self, role_bot):
        """Test should respond when mentioned."""
        msg = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="User",
            content="@test_bot Hello",
            channel_id="chan1",
            timestamp=datetime.now(),
            mentions=["test_bot"]
        )
        
        assert role_bot._should_respond(msg) is True
    
    def test_should_not_respond_to_own_message(self, role_bot):
        """Test should not respond to own message."""
        msg = UnifiedMessage(
            id="1",
            author_id="test_bot",
            author_name="Test Bot",
            content="Hello",
            channel_id="chan1",
            timestamp=datetime.now(),
            mentions=[]
        )
        
        assert role_bot._should_respond(msg) is False
    
    @pytest.mark.asyncio
    async def test_handle_message_updates_context(self, role_bot):
        """Test handle_message updates context."""
        msg = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="User",
            content="@test_bot Hello",
            channel_id="chan1",
            timestamp=datetime.now(),
            mentions=["test_bot"]
        )
        
        with patch.object(role_bot, '_generate_response', new=AsyncMock(return_value="Hi")):
            with patch.object(role_bot, 'send_message', new=AsyncMock()):
                await role_bot.handle_message(msg)
        
        assert len(role_bot.context) == 1
        assert role_bot.context[0].content == "@test_bot Hello"
    
    @pytest.mark.asyncio
    async def test_handle_task_changes_state(self, role_bot):
        """Test handle_task changes bot state."""
        task = CrossChannelTask(
            task_id="task1",
            source_channel="source",
            target_channel="target",
            target_bots=["test_bot"],
            instruction="Test task"
        )
        
        with patch.object(role_bot, 'send_message', new=AsyncMock()):
            await role_bot.handle_task(task)
        
        assert role_bot.state == BotState.DISCUSSING
        assert role_bot.current_task == task


class TestHubListener:
    """Test HubListener functionality."""
    
    @pytest.fixture
    def mock_discord_client(self):
        """Mock Discord client."""
        with patch('ai_toolbox.multi_bot.hub_listener.discord.Client') as mock:
            yield mock
    
    @pytest.fixture
    def hub_listener(self, mock_discord_client):
        """Create HubListener instance."""
        from ai_toolbox.multi_bot.hub_listener import HubListener
        callback = AsyncMock()
        return HubListener(
            token="test_token",
            on_message=callback
        )
    
    def test_initialization(self, hub_listener):
        """Test HubListener initialization."""
        assert hub_listener.token == "test_token"
        assert hub_listener._running is False
    
    @pytest.mark.asyncio
    async def test_start_sets_running(self, hub_listener):
        """Test start sets running flag."""
        with patch.object(hub_listener.client, 'start', new=AsyncMock()):
            await hub_listener.start()
            assert hub_listener._running is True
    
    def test_is_running_before_start(self, hub_listener):
        """Test is_running returns False before start."""
        assert hub_listener.is_running() is False


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_message_flow(self):
        """Test complete message flow."""
        from ai_toolbox.multi_bot.message_bus import MessageBus
        
        # Create bus
        bus = MessageBus()
        
        # Create mock bot
        mock_bot = Mock()
        mock_bot.config = Mock()
        mock_bot.config.bot_id = "test_bot"
        mock_bot.config.channels = ["金銮殿"]
        mock_bot.handle_message = AsyncMock()
        mock_bot.handle_task = AsyncMock()
        
        # Register bot
        bus.register_bot(mock_bot)
        
        # Publish message
        msg = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="User",
            content="@test_bot Hello",
            channel_id="1477312823817277681",
            timestamp=datetime.now(),
            mentions=["test_bot"]
        )
        
        await bus.publish(msg)
        
        # Verify bot received message
        mock_bot.handle_message.assert_called_once()
    
    def test_cross_channel_task_parsing(self):
        """Test cross-channel task parsing."""
        from ai_toolbox.multi_bot.message_bus import MessageBus
        
        bus = MessageBus()
        
        # Message with cross-channel instruction
        msg = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="皇帝",
            content="@丞相 @太尉 去内阁商议",
            channel_id="1477312823817277681",  # 金銮殿
            timestamp=datetime.now(),
            mentions=["chengxiang", "taiwei"]
        )
        
        task = bus._parse_cross_channel_task(msg)
        
        assert task is not None
        assert task.source_channel == "1477312823817277681"
        assert task.target_channel == "1477312823817277682"  # 内阁
        assert "chengxiang" in task.target_bots
        assert "taiwei" in task.target_bots
