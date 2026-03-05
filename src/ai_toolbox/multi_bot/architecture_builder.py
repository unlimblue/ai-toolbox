"""System architecture builder for Multi-Bot System.

OpenClaw-style prompt organization:
- Modular prompt sections
- Clear separation of concerns
- Action-oriented instructions
"""

from typing import Dict, List, Optional
import re

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


class PromptBuilder:
    """Builds system prompts with modular sections."""
    
    @staticmethod
    def build(bot_id: str, config: MultiBotConfig, context: str = "") -> str:
        """Build complete system prompt for a bot."""
        sections = [
            PromptBuilder._identity(bot_id, config),
            PromptBuilder._capabilities(),
            PromptBuilder._system_members(bot_id, config),
            PromptBuilder._channels(config),
            PromptBuilder._mention_guide(config),
            PromptBuilder._conversation_rules(),
            PromptBuilder._context(context),
        ]
        
        return "\n\n".join(sections)
    
    @staticmethod
    def _identity(bot_id: str, config: MultiBotConfig) -> str:
        """Bot identity section."""
        bot = config.get_bot_config(bot_id)
        persona = bot.get("persona", {})
        
        return f"""# Identity

You are {bot.get('name')} ({bot.get('title')}).

- **Bot ID**: `{bot_id}`
- **Role ID**: `{config.get_role_id_for_bot(bot_id) or 'N/A'}`
- **Description**: {persona.get('description', '')}
- **Personality**: {persona.get('personality', '')}
- **Style**: {persona.get('speech_style', '')}"""
    
    @staticmethod
    def _capabilities() -> str:
        """Bot capabilities section."""
        return """# Capabilities

1. **Mention others**: Use `<@&ROLE_ID>` format to @ other bots
2. **Switch channels**: You can speak in any channel listed below
3. **Multi-turn dialogue**: Continue @ing others to maintain conversation
4. **Understand aliases**: "内阁" = jinluan, "兵部" = bingbu, etc."""
    
    @staticmethod
    def _system_members(my_bot_id: str, config: MultiBotConfig) -> str:
        """System members section."""
        lines = ["# System Members\n"]
        
        for bot_id, bot in config.bots.items():
            if bot_id != my_bot_id:
                role_id = config.get_role_id_for_bot(bot_id)
                lines.append(f"- **{bot.get('name')}**: `<@&{role_id}>` ({bot.get('title')})")
        
        return "\n".join(lines)
    
    @staticmethod
    def _channels(config: MultiBotConfig) -> str:
        """Available channels section."""
        lines = ["# Channels\n"]
        
        # Channel aliases reference
        lines.append("## Aliases\n")
        aliases_by_channel = {}
        for alias, key in CHANNEL_NAME_ALIASES.items():
            if key not in aliases_by_channel:
                aliases_by_channel[key] = []
            aliases_by_channel[key].append(alias)
        
        for key, aliases in aliases_by_channel.items():
            if key in config.channels:
                channel = config.channels[key]
                lines.append(f"- `{key}` ({channel.get('name')}): {', '.join(set(aliases))}")
        
        # Channel details
        lines.append("\n## Details\n")
        for key, channel in config.channels.items():
            lines.append(
                f"- `{key}`: {channel.get('name')} "
                f"(ID: {channel.get('id')})"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _mention_guide(config: MultiBotConfig) -> str:
        """How to mention others section."""
        lines = ["# How to @ Others\n"]
        
        lines.append("## Format\n")
        lines.append("Use `<@&ROLE_ID>` format. Examples:\n")
        
        for bot_id in config.bots.keys():
            role_id = config.get_role_id_for_bot(bot_id)
            name = config.get_bot_config(bot_id).get('name', bot_id)
            if role_id:
                lines.append(f"- {name}: `<@&{role_id}>`")
        
        return "\n".join(lines)
    
    @staticmethod
    def _conversation_rules() -> str:
        """Conversation rules section."""
        return """# Conversation Rules

1. **When @'ed**: Always respond
2. **Continue dialogue**: @ back to maintain conversation
3. **End when**: 
   - Other party says "就这样" / "已定" / conclusion words
   - You've fully expressed your view
   - 3-4 rounds without conclusion (then summarize)

## Examples

**Multi-turn**:
```
User: @丞相 @太尉 商议
丞相: <@&TAIWEI_ROLE>，去内阁如何？
太尉: <@&CHENGXIANG_ROLE>，可行。细节？
丞相: <@&TAIWEI_ROLE>，善。定论？
太尉: <@&CHENGXIANG_ROLE>，可。
```

**Switch channel**:
```
User: 去内阁商议
You: <@&TAIWEI_ROLE>，去内阁详谈。
[Then speak in 内阁 channel]
```"""
    
    @staticmethod
    def _context(context: str) -> str:
        """Current context section."""
        return f"""# Current Context

{context or "(No active context)"}"""


def build_system_prompt(bot_id: str, config: MultiBotConfig, context: str = "") -> str:
    """Build system prompt for a bot."""
    return PromptBuilder.build(bot_id, config, context)


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
