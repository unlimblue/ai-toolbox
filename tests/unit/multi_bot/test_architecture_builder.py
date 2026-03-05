"""Tests for architecture builder."""

import pytest
from unittest.mock import Mock

from ai_toolbox.multi_bot.architecture_builder import (
    build_system_architecture_info,
    format_system_prompt,
    parse_mentions_from_content,
)
from ai_toolbox.multi_bot.config_loader import MultiBotConfig


class TestArchitectureBuilder:
    """Test system architecture builder."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=MultiBotConfig)
        
        # Organization
        config.organization = {"name": "Test Dynasty"}
        
        # Bots
        config.bots = {
            "chengxiang": {
                "name": "丞相",
                "title": "三公之首",
                "persona": {
                    "description": "统筹决策",
                    "personality": "深思熟虑",
                    "speech_style": "文言文",
                    "keywords": ["统筹", "决策"],
                    "responsibilities": ["政策制定"]
                }
            },
            "taiwei": {
                "name": "太尉",
                "title": "三公之一",
                "persona": {
                    "description": "安全执行",
                    "personality": "果断坚决",
                    "speech_style": "简洁",
                    "keywords": ["安全", "执行"],
                    "responsibilities": ["军事防务"]
                }
            }
        }
        
        # ID mappings
        config.get_user_id_for_bot = Mock(side_effect=lambda x: {
            "chengxiang": "1477314385713037445",
            "taiwei": "1478216774171365466"
        }.get(x))
        
        config.get_role_id_for_bot = Mock(side_effect=lambda x: {
            "chengxiang": "1477314769764614239",
            "taiwei": "1478217215936430092"
        }.get(x))
        
        config.get_bot_config = Mock(side_effect=lambda x: config.bots.get(x, {}))
        
        # Channels
        config.channels = {
            "jinluan": {
                "id": "1478759781425745940",
                "name": "金銮殿",
                "description": "皇帝召见",
                "allowed_bots": ["chengxiang", "taiwei"]
            },
            "neige": {
                "id": "1477312823817277681",
                "name": "内阁",
                "description": "内阁议事",
                "allowed_bots": ["chengxiang", "taiwei"]
            }
        }
        
        return config
    
    def test_build_architecture_info_for_chengxiang(self, mock_config):
        """Test building architecture info for chengxiang."""
        info = build_system_architecture_info("chengxiang", mock_config)
        
        assert info["bot_id"] == "chengxiang"
        assert info["bot_name"] == "丞相"
        assert info["bot_title"] == "三公之首"
        assert info["bot_user_id"] == "1477314385713037445"
        assert info["bot_role_id"] == "1477314769764614239"
        assert info["organization_name"] == "Test Dynasty"
        
        # Should include other bot info
        assert "太尉" in info["other_bots_info"]
        assert "taiwei" in info["other_bots_info"]
        
        # Should not include self
        assert "丞相" not in info["other_bots_info"]
    
    def test_build_architecture_info_for_taiwei(self, mock_config):
        """Test building architecture info for taiwei."""
        info = build_system_architecture_info("taiwei", mock_config)
        
        assert info["bot_id"] == "taiwei"
        assert info["bot_name"] == "太尉"
        
        # Should include other bot info
        assert "丞相" in info["other_bots_info"]
        assert "chengxiang" in info["other_bots_info"]
    
    def test_role_mention_map_format(self, mock_config):
        """Test role mention map format."""
        info = build_system_architecture_info("chengxiang", mock_config)
        
        # Should contain formatted role mentions
        assert "<@&1477314769764614239>" in info["role_mention_map"]  # 丞相
        assert "<@&1478217215936430092>" in info["role_mention_map"]  # 太尉
    
    def test_user_mention_map_format(self, mock_config):
        """Test user mention map format."""
        info = build_system_architecture_info("chengxiang", mock_config)
        
        # Should contain formatted user mentions
        assert "<@1477314385713037445>" in info["user_mention_map"]  # 丞相
        assert "<@1478216774171365466>" in info["user_mention_map"]  # 太尉
    
    def test_channels_info_format(self, mock_config):
        """Test channels info format."""
        info = build_system_architecture_info("chengxiang", mock_config)
        
        # Should contain channel information
        assert "金銮殿" in info["channels_info"]
        assert "1478759781425745940" in info["channels_info"]
        assert "内阁" in info["channels_info"]
        assert "1477312823817277681" in info["channels_info"]
    
    def test_format_system_prompt(self, mock_config):
        """Test formatting complete system prompt."""
        prompt = format_system_prompt("chengxiang", mock_config, context="测试上下文")
        
        # Should contain bot identity
        assert "丞相" in prompt
        assert "三公之首" in prompt
        assert "chengxiang" in prompt
        
        # Should contain architecture sections
        assert "🆔 你的身份标识" in prompt
        assert "👥 系统成员" in prompt
        assert "📍 可用频道" in prompt
        assert "💬 如何正确 @ 人" in prompt
        
        # Should contain context
        assert "测试上下文" in prompt
        
        # Should contain mention formats
        assert "<@&" in prompt  # Role mention format
        assert "@" in prompt  # User mention format


class TestParseMentionsFromContent:
    """Test parsing mentions from message content."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=MultiBotConfig)
        
        config.get_bot_id_from_role_id = Mock(side_effect=lambda x: {
            "1477314769764614239": "chengxiang",
            "1478217215936430092": "taiwei"
        }.get(x))
        
        config.get_bot_id_from_user_id = Mock(side_effect=lambda x: {
            "1477314385713037445": "chengxiang",
            "1478216774171365466": "taiwei"
        }.get(x))
        
        return config
    
    def test_parse_role_mention(self, mock_config):
        """Test parsing role mention from content."""
        content = "<@&1477314769764614239> 你好"
        mentions = parse_mentions_from_content(content, mock_config)
        
        assert "chengxiang" in mentions
    
    def test_parse_user_mention(self, mock_config):
        """Test parsing user mention from content."""
        content = "<@1478216774171365466> 你好"
        mentions = parse_mentions_from_content(content, mock_config)
        
        assert "taiwei" in mentions
    
    def test_parse_multiple_mentions(self, mock_config):
        """Test parsing multiple mentions."""
        content = "<@&1477314769764614239> <@&1478217215936430092> 商议"
        mentions = parse_mentions_from_content(content, mock_config)
        
        assert "chengxiang" in mentions
        assert "taiwei" in mentions
        assert len(mentions) == 2
    
    def test_parse_unknown_mention(self, mock_config):
        """Test parsing unknown mention (should be ignored)."""
        content = "<@&9999999999999999999> 你好"
        mentions = parse_mentions_from_content(content, mock_config)
        
        assert len(mentions) == 0
    
    def test_parse_no_mentions(self, mock_config):
        """Test parsing content with no mentions."""
        content = "你好，没有@任何人"
        mentions = parse_mentions_from_content(content, mock_config)
        
        assert len(mentions) == 0
