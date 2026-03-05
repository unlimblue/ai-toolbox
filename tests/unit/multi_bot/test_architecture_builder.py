"""Tests for architecture builder (PromptLoader)."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from ai_toolbox.multi_bot.architecture_builder import (
    PromptLoader,
    build_system_prompt,
    resolve_channel_name,
    get_channel_id_from_text,
    parse_mentions_from_content,
    CHANNEL_NAME_ALIASES,
)
from ai_toolbox.multi_bot.config_loader import MultiBotConfig


class TestPromptLoader:
    """Test PromptLoader class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=MultiBotConfig)
        
        config.organization = {"name": "Test Dynasty"}
        
        config.bots = {
            "chengxiang": {
                "name": "丞相",
                "title": "三公之首",
                "persona": {
                    "description": "统筹决策",
                    "personality": "深思熟虑",
                    "speech_style": "文言文",
                }
            },
            "taiwei": {
                "name": "太尉",
                "title": "三公之一",
                "persona": {
                    "description": "安全执行",
                    "personality": "果断",
                    "speech_style": "简洁",
                }
            }
        }
        
        config.get_role_id_for_bot = Mock(side_effect=lambda x: {
            "chengxiang": "1477314769764614239",
            "taiwei": "1478217215936430092"
        }.get(x))
        
        config.get_bot_config = Mock(side_effect=lambda x: config.bots.get(x, {}))
        
        config.channels = {
            "jinluan": {"name": "金銮殿", "id": "1478759781425745940"},
            "neige": {"name": "内阁", "id": "1477312823817277681"},
        }
        config.resolve_channel_id = Mock(side_effect=lambda x: {
            "jinluan": "1478759781425745940",
            "neige": "1477312823817277681"
        }.get(x, x))
        
        return config
    
    def test_substitute_template(self):
        """Test template substitution."""
        loader = PromptLoader()
        template = "Hello {{name}}, your ID is {{id}}"
        variables = {"name": "TestBot", "id": "12345"}
        
        result = loader.substitute_template(template, variables)
        
        assert "Hello TestBot" in result
        assert "your ID is 12345" in result
        assert "{{" not in result
    
    def test_build_mention_examples(self, mock_config):
        """Test building mention examples."""
        loader = PromptLoader()
        examples = loader._build_mention_examples(mock_config)
        
        assert "丞相" in examples
        assert "太尉" in examples
        assert "1477314769764614239" in examples
        assert "1478217215936430092" in examples
    
    def test_build_other_members(self, mock_config):
        """Test building other members section."""
        loader = PromptLoader()
        members = loader._build_other_members("chengxiang", mock_config)
        
        assert "太尉" in members
        assert "1478217215936430092" in members
        assert "丞相" not in members  # Should not include self
    
    def test_build_channel_info(self, mock_config):
        """Test building channel info."""
        loader = PromptLoader()
        info = loader._build_channel_info(mock_config)
        
        assert "金銮殿" in info
        assert "内阁" in info
        assert "1478759781425745940" in info
    
    def test_build_system_prompt_structure(self, mock_config):
        """Test that system prompt has expected structure."""
        loader = PromptLoader()
        prompt = loader.build_system_prompt("chengxiang", mock_config)
        
        # Should contain key sections
        assert "丞相" in prompt
        assert "太尉" in prompt
        assert "1477314769764614239" in prompt  # chengxiang role


class TestChannelResolution:
    """Test channel name resolution."""
    
    def test_resolve_channel_alias(self):
        """Test resolving channel aliases."""
        assert resolve_channel_name("去内阁商议") == "neige"
        assert resolve_channel_name("去兵部") == "bingbu"
        assert resolve_channel_name("金銮殿见") == "jinluan"
    
    def test_resolve_unknown_channel(self):
        """Test resolving unknown channel returns None."""
        assert resolve_channel_name("去unknown") is None
    
    def test_get_channel_id_from_text(self):
        """Test getting channel ID from text."""
        config = Mock()
        config.resolve_channel_id = Mock(return_value="1477312823817277681")
        
        result = get_channel_id_from_text("去内阁", config)
        
        assert result == "1477312823817277681"


class TestParseMentions:
    """Test parsing mentions from content."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock config for mention parsing."""
        config = Mock()
        config.get_bot_id_from_role_id = Mock(side_effect=lambda x: {
            "1477314769764614239": "chengxiang",
            "1478217215936430092": "taiwei"
        }.get(x))
        config.get_bot_id_from_user_id = Mock(side_effect=lambda x: {
            "1477314385713037445": "chengxiang"
        }.get(x))
        return config
    
    def test_parse_role_mention(self, mock_config):
        """Test parsing role mention."""
        content = "<@&1477314769764614239> 你好"
        mentions = parse_mentions_from_content(content, mock_config)
        
        assert "chengxiang" in mentions
    
    def test_parse_user_mention(self, mock_config):
        """Test parsing user mention."""
        content = "<@1477314385713037445> 你好"
        mentions = parse_mentions_from_content(content, mock_config)
        
        assert "chengxiang" in mentions
    
    def test_parse_multiple_mentions(self, mock_config):
        """Test parsing multiple mentions."""
        content = "<@&1477314769764614239> <@&1478217215936430092> 商议"
        mentions = parse_mentions_from_content(content, mock_config)
        
        assert "chengxiang" in mentions
        assert "taiwei" in mentions
        assert len(mentions) == 2


class TestBuildSystemPrompt:
    """Test main build_system_prompt function (legacy)."""
    
    def test_build_system_prompt(self):
        """Test the main builder function."""
        config = Mock(spec=MultiBotConfig)
        config.organization = {"name": "Test"}
        config.bots = {
            "test_bot": {
                "name": "TestBot",
                "title": "Tester",
                "persona": {"description": "Testing"}
            }
        }
        config.get_role_id_for_bot = Mock(return_value="12345")
        config.get_bot_config = Mock(return_value=config.bots["test_bot"])
        config.channels = {}
        
        prompt = build_system_prompt("test_bot", config, "test context")
        
        assert "TestBot" in prompt
        assert "test context" in prompt
