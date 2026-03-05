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
        my_bot_config = config.get_bot_config(my_bot_id)
        my_name = my_bot_config.get('name', my_bot_id)
        my_role_id = config.get_role_id_for_bot(my_bot_id)
        
        lines = ["# System Members\n"]
        lines.append(f"## You\n")
        lines.append(f"- **Name**: {my_name}")
        lines.append(f"- **Bot ID**: `{my_bot_id}`")
        lines.append(f"- **Your Role ID**: `{my_role_id}`")
        lines.append(f"- **When someone @ you**: They will type `<@&{my_role_id}>` or you will see '@{my_name}' in Discord\n")
        
        lines.append("## Other Members\n")
        for bot_id, bot in config.bots.items():
            if bot_id != my_bot_id:
                role_id = config.get_role_id_for_bot(bot_id)
                bot_name = bot.get('name', bot_id)
                lines.append(f"- **{bot_name}** (`{bot_id}`)")
                lines.append(f"  - Role ID: `{role_id}`")
                lines.append(f"  - To @ them: Type `<@&{role_id}>` in your response")
                lines.append(f"  - When they @ you: You will see `<@&{my_role_id}>` or '@{my_name}'")
                lines.append(f"  - Title: {bot.get('title', '')}")
                lines.append("")
        
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
        """Conversation rules section with termination and anti-loop guidance."""
        return """# Conversation Rules

## When to Respond
1. **When @'ed directly**: Always respond immediately
2. **During active conversation**: Continue responding to your conversation partner
3. **In cross-channel tasks**: Respond in the designated channel

## ⚠️ CRITICAL: Avoid Infinite Loops

**When you are @'ed by someone:**
- Respond to acknowledge, but **DO NOT @ them back** unless you need a reply
- Example: If @太尉 says "@丞相，你好", you reply "太尉大人安好" (NO @ back)
- Only @ back if you have a question or need their input

**When @'ing others:**
- @ someone ONLY if you need them to respond
- If you just want to inform/acknowledge, do NOT @ them
- Example of good: "太尉大人所言甚是。" (no @, conversation ends)
- Example of bad: "@太尉，所言甚是。" (@ triggers another reply, causes loop)

## When to @ Others
1. **Need response**: You have a question or need their input
2. **Continue dialogue**: You want to keep the conversation going
3. **Explicit coordination**: You need to coordinate action

**DO NOT @ if:**
- You're just acknowledging or agreeing
- The matter is settled
- You're just saying hello/goodbye

## When to END Conversation (CRITICAL)
You MUST end the conversation by NOT @'ing when:

1. **Conclusion reached**: Both parties agree (e.g., "同意", "可行", "就这样")
2. **Question answered**: You have fully answered their question
3. **Task complete**: The assigned task is finished
4. **No further input needed**: You have nothing more to add
5. **Simple acknowledgment**: You're just saying "ok", "明白了", "好的"

### How to End
Simply do NOT include any `<@&ROLE_ID>` in your response. Just reply normally without @.

## Examples

**Good - No loop (acknowledge without @):**
```
太尉: <@&1477314769764614239>，丞相，此方案如何？
丞相: <@&1478217215936430092>，太尉，我觉得可行，请执行。
太尉: 丞相所言极是，我这就去办。（NO @ - ends here, no loop）
```

**Good - Multi-turn then end:**
```
丞相: <@&1478217215936430092>，去内阁商议？
太尉: <@&1477314769764614239>，好，内阁见。
[In 内阁]
丞相: <@&1478217215936430092>，第一步如何？
太尉: <@&1477314769764614239>，先调兵。
丞相: 善。（NO @ - ends）
```

**Bad - Infinite loop (avoid this):**
```
太尉: <@&1477314769764614239>，你好
丞相: <@&1478217215936430092>，你好  ← @ back causes loop!
太尉: <@&1477314769764614239>，你好 again  ← loop continues!
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
