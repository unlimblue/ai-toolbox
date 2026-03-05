"""Configuration loader for Multi-Bot System."""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class MultiBotConfig:
    """
    Multi-Bot configuration manager.
    
    Loads configuration from YAML file and supports environment variable overrides.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to config file. If None, uses MULTI_BOT_CONFIG env var
                        or defaults to config/multi_bot.yaml
        """
        if config_path is None:
            config_path = os.getenv(
                "MULTI_BOT_CONFIG",
                "config/multi_bot.yaml"
            )
        
        self.config_path = Path(config_path)
        if not self.config_path.is_absolute():
            # Make relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            self.config_path = project_root / self.config_path
        
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and process configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Process environment variable references
        config = self._process_env_vars(config)
        
        return config
    
    def _process_env_vars(self, obj: Any) -> Any:
        """
        Process ${VAR} and ${VAR:-default} references in configuration.
        
        Args:
            obj: Configuration object (dict, list, or scalar)
            
        Returns:
            Processed object with environment variables substituted
        """
        if isinstance(obj, dict):
            return {k: self._process_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._process_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_env_vars(obj)
        return obj
    
    def _substitute_env_vars(self, value: str) -> str:
        """
        Substitute environment variables in string.
        
        Supports:
        - ${VAR} - Replace with env var value
        - ${VAR:-default} - Replace with env var or default if not set
        """
        pattern = r'\$\{([^}]+)\}'
        
        def replace(match):
            var_expr = match.group(1)
            
            # Check for default value syntax: VAR:-default
            if ':-' in var_expr:
                var_name, default = var_expr.split(':-', 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_expr, match.group(0))
        
        return re.sub(pattern, replace, value)
    
    # ==================== Property Accessors ====================
    
    @property
    def organization(self) -> Dict[str, str]:
        """Get organization settings."""
        return self._config.get("organization", {})
    
    @property
    def discord_config(self) -> Dict[str, Any]:
        """Get Discord configuration."""
        return self._config.get("discord", {})
    
    @property
    def bots(self) -> Dict[str, Dict]:
        """Get all bot configurations."""
        return self._config.get("bots", {})
    
    @property
    def channels(self) -> Dict[str, Dict]:
        """Get channel configurations."""
        return self.discord_config.get("channels", {})
    
    @property
    def debug_config(self) -> Dict[str, Any]:
        """Get debug configuration."""
        return self._config.get("debug", {})
    
    @property
    def system_config(self) -> Dict[str, Any]:
        """Get system settings."""
        return self._config.get("system", {})
    
    # ==================== Helper Methods ====================
    
    def get_bot_config(self, bot_id: str) -> Dict:
        """Get configuration for specific bot."""
        return self.bots.get(bot_id, {})
    
    def get_channel_config(self, channel_id_or_name: str) -> Dict:
        """
        Get channel config by ID or name.
        
        Args:
            channel_id_or_name: Channel ID (string) or channel name
            
        Returns:
            Channel configuration dict
        """
        channels = self.channels
        
        # Try by name first
        if channel_id_or_name in channels:
            return channels[channel_id_or_name]
        
        # Try by ID
        for name, config in channels.items():
            if config.get("id") == channel_id_or_name:
                return config
        
        return {}
    
    def resolve_channel_id(self, name: str) -> str:
        """
        Resolve channel name to ID.
        
        Args:
            name: Channel name or ID
            
        Returns:
            Channel ID (or original value if not found)
        """
        config = self.channels.get(name, {})
        return config.get("id", name)
    
    def get_user_id_for_bot(self, bot_id: str) -> Optional[str]:
        """Get Discord user ID for bot_id."""
        mapping = self.discord_config.get("user_id_to_bot", {})
        for user_id, mapped_bot_id in mapping.items():
            if mapped_bot_id == bot_id:
                return user_id
        return None
    
    def get_role_id_for_bot(self, bot_id: str) -> Optional[str]:
        """Get Discord role ID for bot_id."""
        mapping = self.discord_config.get("role_id_to_bot", {})
        for role_id, mapped_bot_id in mapping.items():
            if mapped_bot_id == bot_id:
                return role_id
        return None
    
    def get_bot_id_from_user_id(self, user_id: str) -> Optional[str]:
        """Get bot_id from Discord user ID."""
        return self.discord_config.get("user_id_to_bot", {}).get(user_id)
    
    def get_bot_id_from_role_id(self, role_id: str) -> Optional[str]:
        """Get bot_id from Discord role ID."""
        return self.discord_config.get("role_id_to_bot", {}).get(role_id)
    
    def get_display_name(self, bot_id: str) -> str:
        """Get display name for bot."""
        display_names = self.discord_config.get("bot_display_names", {})
        return display_names.get(bot_id, bot_id)
    
    def get_mention_format_preference(self) -> str:
        """Get mention format preference ('role' or 'user')."""
        return self.discord_config.get("mention_format_preference", "role")
    
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug_config.get("enabled", False)


# Global config instance for caching
_config_instance: Optional[MultiBotConfig] = None


def get_config(config_path: Optional[str] = None) -> MultiBotConfig:
    """
    Get global configuration instance.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        MultiBotConfig instance
    """
    global _config_instance
    
    if _config_instance is None or config_path is not None:
        _config_instance = MultiBotConfig(config_path)
    
    return _config_instance


def reload_config(config_path: Optional[str] = None) -> MultiBotConfig:
    """Reload configuration (useful for hot-reload)."""
    global _config_instance
    _config_instance = MultiBotConfig(config_path)
    return _config_instance
