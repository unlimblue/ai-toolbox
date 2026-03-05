"""System architecture builder for Multi-Bot System.

OpenClaw-style prompt organization:
- Modular prompt sections from markdown files
- Template-based variable substitution
- User-customizable behaviors
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from .config_loader import MultiBotConfig


# Channel name aliases for natural language understanding
CHANNEL_NAME_ALIASES = {
    "金銮殿": "jinluan",
    "大殿": "jinluan", 
    "朝堂": "jinluan",
    "内阁": "neige",
    "议事厅": "neige",
    "商议处": "neige",
    "兵部": "bingbu",
    "军事部": "bingbu",
    "防务处": "bingbu",
}


class PromptLoader:
    """Loads and combines prompt files with template substitution."""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files. 
                        Defaults to prompts/multi_bot relative to this file.
        """
        if prompts_dir is None:
            # Default: prompts/multi_bot relative to this file
            current_file = Path(__file__).parent
            self.prompts_dir = current_file.parent.parent.parent / "prompts" / "multi_bot"
        else:
            self.prompts_dir = Path(prompts_dir)
        
        self.base_dir = self.prompts_dir / "base"
        self.behaviors_dir = self.prompts_dir / "behaviors"
    
    def load_file(self, filename: str, subdir: str = "base") -> str:
        """Load a prompt file."""
        filepath = self.prompts_dir / subdir / filename
        if not filepath.exists():
            return ""
        return filepath.read_text(encoding='utf-8')
    
    def load_yaml(self, filename: str, subdir: str = "behaviors") -> Dict[str, Any]:
        """Load a YAML configuration file."""
        filepath = self.prompts_dir / subdir / filename
        if not filepath.exists():
            return {}
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def substitute_template(self, template: str, variables: Dict[str, str]) -> str:
        """Substitute {{variable}} placeholders in template."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
    
    def build_base_prompt(self, bot_id: str, config: MultiBotConfig) -> str:
        """Build base prompt sections."""
        bot = config.get_bot_config(bot_id)
        persona = bot.get("persona", {})
        
        # Build template variables
        variables = {
            "bot_id": bot_id,
            "bot_name": bot.get("name", bot_id),
            "bot_role_id": config.get_role_id_for_bot(bot_id) or "N/A",
            "bot_title": bot.get("title", ""),
            "persona_description": persona.get("description", ""),
            "persona_personality": persona.get("personality", ""),
            "persona_speech_style": persona.get("speech_style", ""),
            "mention_examples": self._build_mention_examples(config),
            "other_members": self._build_other_members(bot_id, config),
            "channel_info": self._build_channel_info(config),
            "your_role_id": config.get_role_id_for_bot(bot_id) or "N/A",
            "other_role_id": self._get_other_role_id(bot_id, config),
        }
        
        # Load and combine base sections
        sections = []
        
        # 1. Identity
        identity = self.load_file("identity.md")
        if identity:
            sections.append(self.substitute_template(identity, variables))
        
        # 2. Capabilities
        capabilities = self.load_file("capabilities.md")
        if capabilities:
            sections.append(self.substitute_template(capabilities, variables))
        
        # 3. System Members
        members = self.load_file("members.md")
        if members:
            sections.append(self.substitute_template(members, variables))
        
        # 4. Rules
        rules = self.load_file("rules.md")
        if rules:
            sections.append(self.substitute_template(rules, variables))
        
        return "\n\n".join(sections)
    
    def build_custom_instructions(self, bot_id: str, config: MultiBotConfig) -> str:
        """Load custom instructions from config (config-driven roles)."""
        bot = config.get_bot_config(bot_id)
        persona = bot.get("persona", {})
        
        # Get custom_instructions from config
        custom = persona.get("custom_instructions", "")
        
        if custom:
            # Substitute template variables
            variables = {
                "bot_id": bot_id,
                "bot_name": bot.get("name", bot_id),
                "bot_role_id": config.get_role_id_for_bot(bot_id) or "N/A",
                "bot_title": bot.get("title", ""),
                "persona_description": persona.get("description", ""),
                "persona_personality": persona.get("personality", ""),
                "persona_speech_style": persona.get("speech_style", ""),
            }
            return self.substitute_template(custom, variables)
        
        return ""
    
    def build_behavior_prompt(self, behavior_config: Optional[str] = None) -> str:
        """Load behavior configuration."""
        if behavior_config is None:
            behavior_config = "default.yaml"
        
        # Load YAML config
        config = self.load_yaml(behavior_config)
        
        # Convert to prompt section
        sections = []
        
        # Add custom instructions if present
        if "custom_instructions" in config:
            sections.append("# Custom Instructions\n")
            sections.append(config["custom_instructions"])
        
        # Add behavior settings
        settings = []
        for key, value in config.items():
            if key != "custom_instructions":
                settings.append(f"- **{key}**: {value}")
        
        if settings:
            sections.append("# Behavior Settings\n")
            sections.append("\n".join(settings))
        
        return "\n\n".join(sections) if sections else ""
    
    def build_system_prompt(
        self, 
        bot_id: str, 
        config: MultiBotConfig, 
        behavior_config: Optional[str] = None,
        context: str = ""
    ) -> str:
        """
        Build complete system prompt by combining all sections.
        
        Args:
            bot_id: Bot identifier
            config: MultiBotConfig instance
            behavior_config: Behavior configuration file name
            context: Additional context to append
            
        Returns:
            Complete system prompt
        """
        sections = []
        
        # 1. Base prompt (identity, capabilities, rules)
        base = self.build_base_prompt(bot_id, config)
        if base:
            sections.append(base)
        
        # 2. Custom instructions from config (config-driven)
        custom = self.build_custom_instructions(bot_id, config)
        if custom:
            sections.append(custom)
        
        # 3. Behavior configuration
        behavior = self.build_behavior_prompt(behavior_config)
        if behavior:
            sections.append(behavior)
        
        # 4. Current context
        if context:
            sections.append(f"# Current Context\n\n{context}")
        
        return "\n\n---\n\n".join(sections)
    
    def _build_mention_examples(self, config: MultiBotConfig) -> str:
        """Build mention examples for system prompt."""
        lines = []
        for bot_id in config.bots.keys():
            role_id = config.get_role_id_for_bot(bot_id)
            name = config.get_bot_config(bot_id).get('name', bot_id)
            if role_id:
                lines.append(f"- {name}: `<@&{role_id}>`")
        return "\n".join(lines)
    
    def _build_other_members(self, my_bot_id: str, config: MultiBotConfig) -> str:
        """Build other members section."""
        lines = []
        my_role_id = config.get_role_id_for_bot(my_bot_id)
        
        for bot_id, bot in config.bots.items():
            if bot_id != my_bot_id:
                role_id = config.get_role_id_for_bot(bot_id)
                name = bot.get('name', bot_id)
                lines.append(f"- **{name}** (`{bot_id}`)")
                lines.append(f"  - Role ID: `{role_id}`")
                lines.append(f"  - To @ them: Type `<@&{role_id}>`")
                lines.append(f"  - When they @ you: You see `<@&{my_role_id}>` or '@你'")
                lines.append(f"  - Title: {bot.get('title', '')}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _build_channel_info(self, config: MultiBotConfig) -> str:
        """Build channel information section."""
        lines = []
        
        # Aliases
        lines.append("### Aliases\n")
        aliases_by_channel = {}
        for alias, key in CHANNEL_NAME_ALIASES.items():
            if key not in aliases_by_channel:
                aliases_by_channel[key] = []
            aliases_by_channel[key].append(alias)
        
        for key, aliases in aliases_by_channel.items():
            if key in config.channels:
                channel = config.channels[key]
                lines.append(f"- `{key}` ({channel.get('name')}): {', '.join(set(aliases))}")
        
        # Details
        lines.append("\n### Channel IDs\n")
        for key, channel in config.channels.items():
            lines.append(f"- `{key}`: ID `{channel.get('id')}`")
        
        return "\n".join(lines)
    
    def _get_other_role_id(self, my_bot_id: str, config: MultiBotConfig) -> str:
        """Get another bot's role ID for examples."""
        for bot_id in config.bots.keys():
            if bot_id != my_bot_id:
                return config.get_role_id_for_bot(bot_id) or "N/A"
        return "N/A"


# Legacy function for backward compatibility
def build_system_prompt(
    bot_id: str, 
    config: MultiBotConfig, 
    context: str = ""
) -> str:
    """Build system prompt for a bot."""
    loader = PromptLoader()
    return loader.build_system_prompt(bot_id, config, context=context)


# Channel resolution functions
def resolve_channel_name(text: str) -> Optional[str]:
    """Resolve channel alias to config key."""
    for alias, key in CHANNEL_NAME_ALIASES.items():
        if alias in text:
            return key
    return None


def get_channel_id_from_text(text: str, config: MultiBotConfig) -> Optional[str]:
    """Get channel ID from text."""
    key = resolve_channel_name(text)
    if key:
        return config.resolve_channel_id(key)
    return None


def parse_mentions_from_content(content: str, config: MultiBotConfig) -> List[str]:
    """Parse mentions from message content."""
    mentions = []
    
    # Match <@&role_id>
    for match in re.finditer(r'<@&(\d+)>', content):
        bot_id = config.get_bot_id_from_role_id(match.group(1))
        if bot_id:
            mentions.append(bot_id)
    
    # Match <@user_id>
    for match in re.finditer(r'<@(\d+)>', content):
        bot_id = config.get_bot_id_from_user_id(match.group(1))
        if bot_id:
            mentions.append(bot_id)
    
    return mentions
