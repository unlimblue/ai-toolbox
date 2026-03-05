"""Tests for configuration loader."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from ai_toolbox.multi_bot.config_loader import MultiBotConfig, get_config, reload_config


class TestMultiBotConfig:
    """Test MultiBotConfig class."""
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample configuration."""
        return {
            "organization": {
                "name": "Test Org",
                "description": "Test description"
            },
            "discord": {
                "user_id_to_bot": {
                    "111111111": "bot1",
                    "222222222": "bot2"
                },
                "role_id_to_bot": {
                    "333333333": "bot1",
                    "444444444": "bot2"
                },
                "bot_display_names": {
                    "bot1": "Bot One",
                    "bot2": "Bot Two"
                },
                "mention_format_preference": "role",
                "channels": {
                    "channel1": {
                        "id": "999999999",
                        "name": "Channel One",
                        "allowed_bots": ["bot1", "bot2"]
                    }
                }
            },
            "bots": {
                "bot1": {
                    "id": "bot1",
                    "name": "Bot One",
                    "token": "${BOT1_TOKEN}",
                    "channels": ["channel1"]
                },
                "bot2": {
                    "id": "bot2",
                    "name": "Bot Two",
                    "token": "${BOT2_TOKEN:-default_token}",
                    "channels": ["channel1"]
                }
            },
            "debug": {
                "enabled": True,
                "channel_id": "999999999"
            }
        }
    
    @pytest.fixture
    def config_file(self, sample_config, tmp_path):
        """Create a temporary config file."""
        config_path = tmp_path / "test_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(sample_config, f)
        return str(config_path)
    
    def test_load_organization(self, config_file):
        """Test loading organization settings."""
        config = MultiBotConfig(config_file)
        
        assert config.organization["name"] == "Test Org"
        assert config.organization["description"] == "Test description"
    
    def test_load_discord_config(self, config_file):
        """Test loading Discord configuration."""
        config = MultiBotConfig(config_file)
        
        discord = config.discord_config
        assert "user_id_to_bot" in discord
        assert discord["user_id_to_bot"]["111111111"] == "bot1"
    
    def test_load_bots(self, config_file):
        """Test loading bot configurations."""
        config = MultiBotConfig(config_file)
        
        bots = config.bots
        assert "bot1" in bots
        assert bots["bot1"]["name"] == "Bot One"
    
    def test_get_bot_config(self, config_file):
        """Test getting specific bot configuration."""
        config = MultiBotConfig(config_file)
        
        bot1_config = config.get_bot_config("bot1")
        assert bot1_config["name"] == "Bot One"
        assert bot1_config["id"] == "bot1"
        
        # Non-existent bot
        assert config.get_bot_config("nonexistent") == {}
    
    def test_get_channel_config_by_name(self, config_file):
        """Test getting channel config by name."""
        config = MultiBotConfig(config_file)
        
        channel = config.get_channel_config("channel1")
        assert channel["id"] == "999999999"
        assert channel["name"] == "Channel One"
    
    def test_get_channel_config_by_id(self, config_file):
        """Test getting channel config by ID."""
        config = MultiBotConfig(config_file)
        
        channel = config.get_channel_config("999999999")
        assert channel["name"] == "Channel One"
    
    def test_resolve_channel_id(self, config_file):
        """Test resolving channel name to ID."""
        config = MultiBotConfig(config_file)
        
        assert config.resolve_channel_id("channel1") == "999999999"
        # Unknown channel returns original
        assert config.resolve_channel_id("unknown") == "unknown"
    
    def test_env_var_substitution(self, config_file):
        """Test environment variable substitution."""
        os.environ["BOT1_TOKEN"] = "secret_token_123"
        
        try:
            config = MultiBotConfig(config_file)
            bot1 = config.get_bot_config("bot1")
            assert bot1["token"] == "secret_token_123"
        finally:
            del os.environ["BOT1_TOKEN"]
    
    def test_env_var_default(self, config_file):
        """Test environment variable with default."""
        # BOT2_TOKEN not set, should use default
        config = MultiBotConfig(config_file)
        bot2 = config.get_bot_config("bot2")
        assert bot2["token"] == "default_token"
    
    def test_get_user_id_for_bot(self, config_file):
        """Test getting user ID for bot."""
        config = MultiBotConfig(config_file)
        
        assert config.get_user_id_for_bot("bot1") == "111111111"
        assert config.get_user_id_for_bot("nonexistent") is None
    
    def test_get_role_id_for_bot(self, config_file):
        """Test getting role ID for bot."""
        config = MultiBotConfig(config_file)
        
        assert config.get_role_id_for_bot("bot1") == "333333333"
        assert config.get_role_id_for_bot("nonexistent") is None
    
    def test_get_bot_id_from_user_id(self, config_file):
        """Test getting bot ID from user ID."""
        config = MultiBotConfig(config_file)
        
        assert config.get_bot_id_from_user_id("111111111") == "bot1"
        assert config.get_bot_id_from_user_id("999999999") is None
    
    def test_get_bot_id_from_role_id(self, config_file):
        """Test getting bot ID from role ID."""
        config = MultiBotConfig(config_file)
        
        assert config.get_bot_id_from_role_id("333333333") == "bot1"
        assert config.get_bot_id_from_role_id("999999999") is None
    
    def test_get_display_name(self, config_file):
        """Test getting display name for bot."""
        config = MultiBotConfig(config_file)
        
        assert config.get_display_name("bot1") == "Bot One"
        assert config.get_display_name("unknown") == "unknown"
    
    def test_get_mention_format_preference(self, config_file):
        """Test getting mention format preference."""
        config = MultiBotConfig(config_file)
        
        assert config.get_mention_format_preference() == "role"
    
    def test_is_debug_enabled(self, config_file):
        """Test checking if debug is enabled."""
        config = MultiBotConfig(config_file)
        
        assert config.is_debug_enabled() is True
    
    def test_file_not_found(self):
        """Test handling of missing config file."""
        with pytest.raises(FileNotFoundError):
            MultiBotConfig("/nonexistent/path/config.yaml")
    
    def test_channels_property(self, config_file):
        """Test channels property."""
        config = MultiBotConfig(config_file)
        
        channels = config.channels
        assert "channel1" in channels
        assert channels["channel1"]["id"] == "999999999"
    
    def test_system_config(self, config_file):
        """Test system configuration access."""
        # Add system config to fixture
        config = MultiBotConfig(config_file)
        
        # Should return empty dict if not present
        assert isinstance(config.system_config, dict)


class TestConfigGlobalFunctions:
    """Test global config functions."""
    
    @pytest.fixture(autouse=True)
    def reset_global_config(self):
        """Reset global config before each test."""
        import ai_toolbox.multi_bot.config_loader as config_module
        config_module._config_instance = None
        yield
        config_module._config_instance = None
    
    def test_get_config_creates_instance(self, tmp_path):
        """Test that get_config creates global instance."""
        config_path = tmp_path / "test.yaml"
        with open(config_path, 'w') as f:
            yaml.dump({"organization": {"name": "Test"}}, f)
        
        config1 = get_config(str(config_path))
        config2 = get_config()  # Should return same instance
        
        assert config1 is config2
    
    def test_reload_config(self, tmp_path):
        """Test reloading configuration."""
        config_path = tmp_path / "test.yaml"
        with open(config_path, 'w') as f:
            yaml.dump({"organization": {"name": "Original"}}, f)
        
        config1 = get_config(str(config_path))
        assert config1.organization["name"] == "Original"
        
        # Modify file
        with open(config_path, 'w') as f:
            yaml.dump({"organization": {"name": "Updated"}}, f)
        
        # Reload
        config2 = reload_config(str(config_path))
        assert config2.organization["name"] == "Updated"


class TestRealConfig:
    """Test with real configuration file."""
    
    def test_load_cyber_dynasty_config(self):
        """Test loading actual Cyber Dynasty configuration."""
        # Use actual config file
        config = MultiBotConfig("config/multi_bot.yaml")
        
        assert config.organization["name"] == "赛博王朝"
        assert "chengxiang" in config.bots
        assert "taiwei" in config.bots
        
        # Check channel resolution
        assert config.resolve_channel_id("jinluan") == "1478759781425745940"
        assert config.resolve_channel_id("neige") == "1477312823817277681"
        
        # Check ID mappings
        assert config.get_bot_id_from_role_id("1477314769764614239") == "chengxiang"
        assert config.get_bot_id_from_role_id("1478217215936430092") == "taiwei"
