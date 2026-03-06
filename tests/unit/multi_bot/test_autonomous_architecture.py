"""Tests for autonomous decision architecture."""

import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from ai_toolbox.multi_bot.role_bot import RoleBot
from ai_toolbox.multi_bot.message_bus import MessageBus
from ai_toolbox.multi_bot.graph_manager import ContextGraphManager
from ai_toolbox.multi_bot.models import UnifiedMessage, BotConfig, BotPersona


class TestAutonomousRoleBot:
    """Test RoleBot autonomous decision-making."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock bot config."""
        persona = Mock(spec=BotPersona)
        persona.name = "丞相"
        persona.description = "监督者"
        persona.system_prompt = "你是丞相"
        
        config = Mock(spec=BotConfig)
        config.bot_id = "chengxiang"
        config.token_env = "TEST_TOKEN"
        config.api_key_env = "TEST_API_KEY"
        config.model_provider = "kimi"
        config.model_name = "kimi-k2-5"
        config.persona = persona
        
        return config
    
    @pytest.fixture
    def mock_graph_manager(self):
        """Create mock graph manager."""
        gm = Mock(spec=ContextGraphManager)
        gm.get_context_for_bot = Mock(return_value=Mock(
            nodes={},
            get_linear_history=Mock(return_value="历史对话")
        ))
        return gm
    
    @pytest.fixture
    def role_bot(self, mock_config, mock_graph_manager):
        """Create RoleBot instance."""
        return RoleBot(config=mock_config, graph_manager=mock_graph_manager)
    
    @pytest.mark.asyncio
    async def test_handle_message_skips_own_message(self, role_bot):
        """Test that bot skips its own messages."""
        message = Mock(spec=UnifiedMessage)
        message.id = "msg_1"
        message.author_id = "chengxiang"  # Same as bot_id
        message.author_name = "丞相"
        message.content = "测试"
        message.channel_id = "ch_1"
        message.timestamp = Mock()
        
        with patch.object(role_bot, '_send_debug') as mock_debug:
            await role_bot.handle_message(message, "graph_1")
            mock_debug.assert_called_with("⏭️ Skipping own message")
    
    @pytest.mark.asyncio
    async def test_build_decision_prompt(self, role_bot):
        """Test decision prompt building."""
        message = Mock(spec=UnifiedMessage)
        message.author_name = "皇帝"
        message.content = "去内阁通知太尉"
        message.channel_id = "1478759781425745940"
        
        prompt = role_bot._build_decision_prompt(message, "历史对话")
        
        assert "皇帝" in prompt
        assert "去内阁通知太尉" in prompt
        assert "历史对话" in prompt
        assert "actions" in prompt
        assert "JSON" in prompt
    
    @pytest.mark.asyncio
    async def test_ai_decide_parses_json(self, role_bot):
        """Test AI decision parsing."""
        mock_response = Mock()
        mock_response.content = '''```json
        {
          "actions": [
            {
              "channel_id": "1477312823817277681",
              "content": "@太尉 请前来",
              "reason": "通知"
            }
          ]
        }
        ```'''
        
        # Mock the API key
        with patch.dict(os.environ, {"TEST_API_KEY": "fake_key"}):
            with patch('ai_toolbox.multi_bot.role_bot.create_provider') as mock_provider:
                mock_client = Mock()
                mock_client.chat = AsyncMock(return_value=mock_response)
                mock_provider.return_value = mock_client
                
                actions = await role_bot._ai_decide("prompt")
                
                assert len(actions) == 1
                assert actions[0]["channel_id"] == "1477312823817277681"
                assert "@太尉" in actions[0]["content"]


class TestSimplifiedMessageBus:
    """Test simplified MessageBus without hardcoded parsing."""
    
    @pytest.fixture
    def message_bus(self):
        """Create MessageBus instance."""
        return MessageBus()
    
    @pytest.fixture
    def mock_message(self):
        """Create mock message."""
        message = Mock(spec=UnifiedMessage)
        message.id = "msg_1"
        message.author_id = "user_1"
        message.author_name = "皇帝"
        message.content = "@丞相 去内阁通知太尉"
        message.channel_id = "1478759781425745940"
        message.mentions = ["chengxiang"]
        message.timestamp = Mock()
        return message
    
    @pytest.mark.asyncio
    async def test_publish_adds_to_graph(self, message_bus, mock_message):
        """Test that publish adds message to ContextGraph."""
        message_bus.graph_manager.add_message_to_graph = Mock()
        
        with patch.object(message_bus, '_send_debug'):
            await message_bus.publish(mock_message)
            
            message_bus.graph_manager.add_message_to_graph.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_forwards_to_mentioned_bots(self, message_bus, mock_message):
        """Test that publish forwards to mentioned bots only."""
        mock_bot = Mock()
        mock_bot.handle_message = AsyncMock()
        message_bus.register_bot("chengxiang", mock_bot)
        message_bus.graph_manager.add_message_to_graph = Mock()
        
        with patch.object(message_bus, '_send_debug'):
            await message_bus.publish(mock_message)
            
            mock_bot.handle_message.assert_called_once()
    
    def test_no_hardcoded_channel_parsing(self, message_bus):
        """Verify no hardcoded channel aliases exist."""
        # Check that _parse_cross_channel_task method doesn't exist
        assert not hasattr(message_bus, '_parse_cross_channel_task')
        
        # Check that publish doesn't have hardcoded logic
        import inspect
        source = inspect.getsource(message_bus.publish)
        assert "金銮殿" not in source
        assert "内阁" not in source
        assert "兵部" not in source


class TestContextGraphIntegration:
    """Test ContextGraph integration with autonomous bot."""
    
    def test_graph_manager_auto_visibility(self):
        """Test that visibility is calculated automatically."""
        from ai_toolbox.multi_bot.graph_manager import ContextGraphManager
        from datetime import datetime
        
        gm = ContextGraphManager()
        
        # Add message mentioning specific bot
        gm.add_message_to_graph(
            graph_id="test_graph",
            message_id="msg_1",
            author_id="user_1",
            author_name="皇帝",
            content="@丞相 测试",
            channel_id="ch_1",
            timestamp=datetime.now(),
            mention_targets=["chengxiang"]
        )
        
        # Get context for mentioned bot
        subgraph = gm.extract_subgraph("test_graph", "chengxiang")
        
        # Bot should see the message
        assert len(subgraph.nodes) > 0
    
    def test_multi_channel_support(self):
        """Test that contexts from multiple channels can be retrieved."""
        from ai_toolbox.multi_bot.graph_manager import ContextGraphManager
        from datetime import datetime
        
        gm = ContextGraphManager()
        
        # Add messages to different channel graphs
        for channel_id, graph_id in [
            ("ch_jinluan", "channel_ch_jinluan"),
            ("ch_neige", "channel_ch_neige")
        ]:
            gm.add_message_to_graph(
                graph_id=graph_id,
                message_id=f"msg_{channel_id}",
                author_id="user_1",
                author_name="皇帝",
                content=f"Message in {channel_id}",
                channel_id=channel_id,
                timestamp=datetime.now(),
                mention_targets=["chengxiang"]
            )
        
        # Get context for each channel separately
        context_jinluan = gm.extract_subgraph("channel_ch_jinluan", "chengxiang")
        context_neige = gm.extract_subgraph("channel_ch_neige", "chengxiang")
        
        assert len(context_jinluan.nodes) > 0
        assert len(context_neige.nodes) > 0
