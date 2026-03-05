"""Integration tests for cross-channel coordination and state machine."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_toolbox.multi_bot.models import (
    UnifiedMessage,
    CrossChannelTask,
    BotState,
    BotPersona,
    BotConfig,
)
from ai_toolbox.multi_bot.message_bus import MessageBus
from ai_toolbox.multi_bot.role_bot import RoleBot
from ai_toolbox.multi_bot.config import DYNASTY_CONFIG


class TestCrossChannelCoordination:
    """Test cross-channel task coordination."""
    
    @pytest.fixture
    def message_bus(self):
        """Create MessageBus with fresh state."""
        return MessageBus()
    
    @pytest.fixture
    def mock_chengxiang(self):
        """Create mock 丞相 bot."""
        bot = Mock()
        bot.config = Mock()
        bot.config.bot_id = "chengxiang"
        bot.config.channels = ["金銮殿", "内阁"]
        bot.handle_message = AsyncMock()
        bot.handle_task = AsyncMock()
        return bot
    
    @pytest.fixture
    def mock_taiwei(self):
        """Create mock 太尉 bot."""
        bot = Mock()
        bot.config = Mock()
        bot.config.bot_id = "taiwei"
        bot.config.channels = ["金銮殿", "内阁", "兵部"]
        bot.handle_message = AsyncMock()
        bot.handle_task = AsyncMock()
        return bot
    
    @pytest.mark.asyncio
    async def test_cross_channel_task_creation(self, message_bus, mock_chengxiang, mock_taiwei):
        """Test cross-channel task is created when emperor sends instruction."""
        # Register bots
        message_bus.register_bot(mock_chengxiang)
        message_bus.register_bot(mock_taiwei)
        
        # Emperor sends cross-channel instruction
        msg = UnifiedMessage(
            id="1",
            author_id="1477269928720466011",
            author_name="皇帝",
            content="@丞相 @太尉，去内阁商议边防方案，回禀结果",
            channel_id="1478759781425745940",  # 金銮殿
            timestamp=datetime.now(),
            mentions=["chengxiang", "taiwei"]
        )
        
        await message_bus.publish(msg)
        
        # Verify task was created
        assert len(message_bus.active_tasks) == 1
        task = list(message_bus.active_tasks.values())[0]
        assert task.source_channel == "1478759781425745940"
        assert task.target_channel == "1477312823817277681"  # 内阁
        assert "chengxiang" in task.target_bots
        assert "taiwei" in task.target_bots
    
    @pytest.mark.asyncio
    async def test_bots_receive_task_notification(self, message_bus, mock_chengxiang, mock_taiwei):
        """Test bots receive notification when task is created."""
        message_bus.register_bot(mock_chengxiang)
        message_bus.register_bot(mock_taiwei)
        
        msg = UnifiedMessage(
            id="1",
            author_id="1477269928720466011",
            author_name="皇帝",
            content="@丞相 @太尉，去内阁商议",
            channel_id="1478759781425745940",
            timestamp=datetime.now(),
            mentions=["chengxiang", "taiwei"]
        )
        
        await message_bus.publish(msg)
        
        # Both bots should receive task notification
        mock_chengxiang.handle_task.assert_called_once()
        mock_taiwei.handle_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_no_task_for_same_channel(self, message_bus, mock_chengxiang):
        """Test no task created when target is same as source."""
        message_bus.register_bot(mock_chengxiang)
        
        # Message asking to go to same channel
        msg = UnifiedMessage(
            id="1",
            author_id="1477269928720466011",
            author_name="皇帝",
            content="@丞相 在内阁商议",  # Already in 内阁
            channel_id="1477312823817277681",  # 内阁
            timestamp=datetime.now(),
            mentions=["chengxiang"]
        )
        
        await message_bus.publish(msg)
        
        # No task should be created
        assert len(message_bus.active_tasks) == 0


class TestBotStateMachine:
    """Test bot state machine transitions."""
    
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
            channels=["金銮殿", "内阁"],
            persona=BotPersona(
                name="Test",
                description="Test bot",
                system_prompt="You are a test bot"
            )
        )
    
    @pytest.fixture
    def role_bot(self, bot_config):
        """Create RoleBot instance."""
        with patch.dict('os.environ', {'TEST_TOKEN': 'test_token_123'}):
            return RoleBot(bot_config)
    
    def test_initial_state_is_idle(self, role_bot):
        """Test bot starts in IDLE state."""
        assert role_bot.state == BotState.IDLE
        assert role_bot.current_task is None
    
    @pytest.mark.asyncio
    async def test_idle_to_discussing_transition(self, role_bot):
        """Test transition from IDLE to DISCUSSING when task received."""
        task = CrossChannelTask(
            task_id="task-123",
            source_channel="1478759781425745940",
            target_channel="1477312823817277681",
            target_bots=["test_bot"],
            instruction="Test task"
        )
        
        with patch.object(role_bot, 'send_message', new=AsyncMock()):
            await role_bot.handle_task(task)
        
        assert role_bot.state == BotState.DISCUSSING
        assert role_bot.current_task == task
    
    @pytest.mark.asyncio
    async def test_discussing_to_reporting_transition(self, role_bot):
        """Test transition from DISCUSSING to REPORTING when conclusion formed."""
        # First set up task
        task = CrossChannelTask(
            task_id="task-123",
            source_channel="1478759781425745940",
            target_channel="1477312823817277681",
            target_bots=["test_bot"],
            instruction="Test task"
        )
        
        with patch.object(role_bot, 'send_message', new=AsyncMock()):
            await role_bot.handle_task(task)
        
        assert role_bot.state == BotState.DISCUSSING
        
        # Simulate discussion
        for i in range(10):
            msg = UnifiedMessage(
                id=str(i),
                author_id="other_bot",
                author_name="Other Bot",
                content=f"Message {i}",
                channel_id="1477312823817277681",
                timestamp=datetime.now(),
                mentions=[]
            )
            role_bot.context_filter.add_message(msg)
        
        # Trigger conclusion
        conclusion_msg = UnifiedMessage(
            id="11",
            author_id="other_bot",
            author_name="Other Bot",
            content="结论：我们同意这个方案",
            channel_id="1477312823817277681",
            timestamp=datetime.now(),
            mentions=[]
        )
        
        with patch.object(role_bot, '_form_conclusion', new=AsyncMock()):
            role_bot._check_conclusion(conclusion_msg)
            # State transition happens asynchronously
            await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_reporting_to_idle_transition(self, role_bot):
        """Test transition from REPORTING to IDLE after conclusion."""
        task = CrossChannelTask(
            task_id="task-123",
            source_channel="1478759781425745940",
            target_channel="1477312827277681",
            target_bots=["test_bot"],
            instruction="Test task"
        )
        role_bot.current_task = task
        role_bot.state = BotState.REPORTING
        
        # Add some context
        role_bot.context_filter.add_message(
            UnifiedMessage(
                id="1",
                author_id="user1",
                author_name="User",
                content="Test discussion",
                channel_id="1477312823817277681",
                timestamp=datetime.now(),
                mentions=[]
            )
        )
        
        # Mock AI response
        with patch.object(role_bot, 'send_message', new=AsyncMock()):
            with patch('ai_toolbox.multi_bot.role_bot.create_provider') as mock_create:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.content = "我们决定采纳这个方案"
                mock_client.chat = AsyncMock(return_value=mock_response)
                mock_create.return_value = mock_client
                
                await role_bot._form_conclusion()
        
        # Should be back to IDLE
        assert role_bot.state == BotState.IDLE
        assert role_bot.current_task is None
        assert len(role_bot.context_filter.context) == 0


class TestCrossChannelFlow:
    """Test complete cross-channel conversation flow."""
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test complete flow: 金銮殿 -> 内阁 -> 金銮殿."""
        bus = MessageBus()
        
        # Track messages
        messages_sent = []
        
        async def track_send(channel_id, content):
            messages_sent.append({
                'channel': channel_id,
                'content': content
            })
        
        # Create and register bots with mocked send
        with patch.dict('os.environ', {
            'CHENGXIANG_BOT_TOKEN': 'token1',
            'TAIWEI_BOT_TOKEN': 'token2',
            'KIMI_API_KEY': 'api_key'
        }):
            chengxiang_config = DYNASTY_CONFIG.bots["chengxiang"]
            taiwei_config = DYNASTY_CONFIG.bots["taiwei"]
            
            chengxiang = RoleBot(chengxiang_config)
            taiwei = RoleBot(taiwei_config)
            
            # Mock send methods
            chengxiang.send_message = track_send
            taiwei.send_message = track_send
            
            bus.register_bot(chengxiang)
            bus.register_bot(taiwei)
        
        # Step 1: Emperor initiates task in 金銮殿
        emperor_msg = UnifiedMessage(
            id="1",
            author_id="1477269928720466011",
            author_name="皇帝",
            content="@丞相 @太尉，去内阁商议边防方案",
            channel_id="1478759781425745940",
            timestamp=datetime.now(),
            mentions=["chengxiang", "taiwei"]
        )
        
        await bus.publish(emperor_msg)
        
        # Verify task was created
        assert len(bus.active_tasks) == 1
        task = list(bus.active_tasks.values())[0]
        
        # Step 2: Both bots should acknowledge
        # (They send messages via mocked send_message)
        
        # Step 3: Simulate discussion in 内阁
        discussion_msgs = [
            UnifiedMessage(
                id="2",
                author_id="chengxiang",
                author_name="丞相",
                content="奉陛下旨意，来此商议",
                channel_id="1477312823817277681",
                timestamp=datetime.now(),
                mentions=[]
            ),
            UnifiedMessage(
                id="3",
                author_id="taiwei",
                author_name="太尉",
                content="丞相有何高见？",
                channel_id="1477312823817277681",
                timestamp=datetime.now(),
                mentions=["chengxiang"]
            ),
            UnifiedMessage(
                id="4",
                author_id="chengxiang",
                author_name="丞相",
                content="我认为应当加强巡逻",
                channel_id="1477312823817277681",
                timestamp=datetime.now(),
                mentions=[]
            ),
        ]
        
        for msg in discussion_msgs:
            await bus.publish(msg)
        
        # Step 4: Trigger conclusion
        conclusion_trigger = UnifiedMessage(
            id="5",
            author_id="taiwei",
            author_name="太尉",
            content="结论：加强边境巡逻，增派三千精兵",
            channel_id="1477312823817277681",
            timestamp=datetime.now(),
            mentions=[]
        )
        
        await bus.publish(conclusion_trigger)


class TestContextIsolation:
    """Test that each bot has isolated context."""
    
    def test_context_isolation_between_bots(self):
        """Test that each bot maintains separate context."""
        from ai_toolbox.multi_bot.context_filter import ContextFilter
        
        filter1 = ContextFilter("bot1")
        filter2 = ContextFilter("bot2")
        
        # Add message relevant to bot1
        msg1 = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="User",
            content="@bot1 Hello",
            channel_id="chan1",
            timestamp=datetime.now(),
            mentions=["bot1"]
        )
        
        filter1.add_message(msg1)
        filter2.add_message(msg1)
        
        # Only bot1 should have context
        assert len(filter1.context) == 1
        assert len(filter2.context) == 0
    
    def test_context_stats(self):
        """Test context statistics."""
        from ai_toolbox.multi_bot.context_filter import ContextFilter
        
        filter = ContextFilter("test_bot")
        
        # Add various messages
        messages = [
            UnifiedMessage("1", "user1", "User", "@test_bot Hi", "chan1", datetime.now(), ["test_bot"]),
            UnifiedMessage("2", "test_bot", "Test Bot", "Hello", "chan1", datetime.now(), []),
            UnifiedMessage("3", "user2", "User2", "@test_bot Question", "chan2", datetime.now(), ["test_bot"]),
        ]
        
        for msg in messages:
            filter.add_message(msg)
        
        stats = filter.get_stats()
        
        assert stats["total_messages"] == 3
        assert stats["mentions"] == 2
        assert stats["own_messages"] == 1
        assert stats["channels"] == 2


class TestMessageDistribution:
    """Test message distribution logic."""
    
    @pytest.mark.asyncio
    async def test_message_delivered_to_mentioned_bots(self):
        """Test messages are delivered to mentioned bots."""
        bus = MessageBus()
        
        mock_bot = Mock()
        mock_bot.config = Mock()
        mock_bot.config.bot_id = "target_bot"
        mock_bot.config.channels = []
        mock_bot.handle_message = AsyncMock()
        
        bus.register_bot(mock_bot)
        
        msg = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="User",
            content="@target_bot Hello",
            channel_id="chan1",
            timestamp=datetime.now(),
            mentions=["target_bot"]
        )
        
        await bus.publish(msg)
        
        mock_bot.handle_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_message_delivered_to_channel_bots(self):
        """Test messages are delivered to bots in the same channel."""
        bus = MessageBus()
        
        mock_bot = Mock()
        mock_bot.config = Mock()
        mock_bot.config.bot_id = "channel_bot"
        mock_bot.config.channels = ["金銮殿"]
        mock_bot.handle_message = AsyncMock()
        
        bus.register_bot(mock_bot)
        
        msg = UnifiedMessage(
            id="1",
            author_id="user1",
            author_name="User",
            content="General message",  # No mention
            channel_id="1478759781425745940",  # 金銮殿
            timestamp=datetime.now(),
            mentions=[]
        )
        
        await bus.publish(msg)
        
        mock_bot.handle_message.assert_called_once()
