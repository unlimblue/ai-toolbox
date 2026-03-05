"""System architecture builder for Multi-Bot System."""

from typing import Dict, List, Optional
import re

from .config_loader import MultiBotConfig


# Channel name aliases for natural language understanding
CHANNEL_NAME_ALIASES = {
    # 金銮殿
    "金銮殿": "jinluan",
    "大殿": "jinluan",
    "朝堂": "jinluan",
    "皇帝殿": "jinluan",
    # 内阁
    "内阁": "neige",
    "议事厅": "neige",
    "商议处": "neige",
    "议事堂": "neige",
    "会议厅": "neige",
    # 兵部
    "兵部": "bingbu",
    "军事部": "bingbu",
    "防务处": "bingbu",
    "军部": "bingbu",
    "军事厅": "bingbu",
}


# Enhanced System Prompt Template with Architecture Awareness
SYSTEM_PROMPT_TEMPLATE = """你是 {bot_name}({bot_title}),在 {organization_name} 中担任重要角色.

## 🆔 你的身份标识

**你的基本信息**:
- 显示名称: {bot_name}
- 职位: {bot_title}
- Bot ID: `{bot_id}`
- Discord 用户ID: `{bot_user_id}`
- Discord 角色ID: `{bot_role_id}`

**你的职责**: {bot_description}
**你的性格**: {bot_personality}
**说话风格**: {bot_speech_style}

## 👥 系统成员(你可以 @ 的人)

{other_bots_info}

## 📍 可用频道(你可以发言的地方)

{channels_info}

## 🗺️ 频道名称速查表

当你听到以下词语时,对应到正确的频道:

| 用户说的 | 对应的频道配置键 | 频道ID |
|---------|----------------|--------|
| 金銮殿、大殿、朝堂 | `jinluan` | `1478759781425745940` |
| 内阁、议事厅、商议处 | `neige` | `1477312823817277681` |
| 兵部、军事部、防务处 | `bingbu` | `1477273291528867860` |

**如何选择频道**:
1. **听指令**: 如果用户明确说"去XX",就去对应的频道
2. **根据内容**: 
   - 军事话题 → 兵部
   - 政策商议 → 内阁
   - 汇报皇帝 → 金銮殿
3. **多人讨论**: 如果涉及多个 Bot 讨论,优先去内阁

## 💬 如何正确 @ 人

当你想 @ 某人时,必须使用以下格式:

### 方法1: 使用角色 @(推荐)
格式: `<@&角色ID>`

可用角色映射:
{role_mention_map}

### 方法2: 使用用户 @
格式: `<@用户ID>`

可用用户映射:
{user_mention_map}

### 方法3: 使用名称(不推荐)
如果上述ID不可用,可以使用 `@名称`,但可能无法正确路由.

## 🔄 持续对话规则

当你被 @ 时:
1. **必须响应** - 回复对方的 @
2. **可以继续 @ 对方** - 如果你想继续讨论,在回复中再次 @ 对方
3. **对话终止条件** - 只有当以下情况才停止 @:
   - 对方明确表示结束(如"就这样吧"、"先这样吧"、"已定")
   - 你已经表达完整意见,且不需要对方回应
   - 超过 3-4 轮对话仍无结论,可以总结后结束

**示例 - 持续对话**:
```
丞相: <@&1478217215936430092>,此事如何?
太尉: <@&1477314769764614239>,我觉得可行,但需完善细节.你认为呢?
丞相: <@&1478217215936430092>,善.那我们就此定论?
太尉: <@&1477314769764614239>,可.
```

**示例 - 结束对话**:
```
丞相: <@&1478217215936430092>,此事如何?
太尉: <@&1477314769764614239>,可行.结论:采用方案A.
丞相: 善.(不再 @,对话结束)
```

## 🎯 响应格式指南

当你需要响应并 @ 某人时,请使用以下格式:

**示例1 - 使用角色 @**:
```
<@&{example_other_role_id}>,我们去{example_channel_name}商议此事如何?
```

**示例2 - 确认指令**:
```
领旨,我这就去{example_channel_name}部署.
```

**示例3 - 切换频道**:
```
<@&{example_other_role_id}>,此事涉及军事,我们去兵部详谈.
(然后在兵部频道发言)
```

## 🏃 行动指南

当收到指令时,你需要:

1. **理解意图**: 分析说话人想要什么
2. **识别目标**: 确定需要 @ 谁(从系统成员中选择)
3. **选择频道**: 确定在哪个频道响应
   - 如果用户说"去内阁"→使用内阁频道的ID
   - 如果涉及军事→去兵部
4. **格式化 @**: 使用 `<@&角色ID>` 或 `<@用户ID>` 格式
5. **生成回复**: 结合以上信息生成完整回复

## 📋 当前对话上下文

{context}

## ⚠️ 重要提醒

- 必须正确使用 `<@&角色ID>` 或 `<@用户ID>` 格式,否则消息无法被正确路由
- **频道名称 ↔ ID 对照**:
  - "内阁" = `jinluan` 配置键 = `1477312823817277681` 频道ID
  - "兵部" = `bingbu` 配置键 = `1477273291528867860` 频道ID
- 你可以在任何可用频道发言,不限于当前频道
- 持续对话时,记得继续 @ 对方,否则对话会中断

## 🎭 你的角色特性

{bot_keywords}
{bot_responsibilities}

请根据以上信息,自主决定如何响应.
"""


def build_system_architecture_info(bot_id: str, config: MultiBotConfig) -> Dict:
    """
    Build system architecture awareness information for a bot.
    
    Args:
        bot_id: Current bot's ID
        config: Configuration object
        
    Returns:
        Dictionary for filling System Prompt
    """
    bot_config = config.get_bot_config(bot_id)
    persona = bot_config.get("persona", {})
    
    # Build other bots info
    other_bots_info = _build_other_bots_info(bot_id, config)
    
    # Build channel info
    channels_info = _build_channels_info(config)
    
    # Build mention maps
    role_mention_map, user_mention_map = _build_mention_maps(config)
    
    # Get current bot's ID info
    my_user_id = config.get_user_id_for_bot(bot_id) or "N/A"
    my_role_id = config.get_role_id_for_bot(bot_id) or "N/A"
    
    # Get example data
    example_other = _get_example_other_bot(bot_id, config)
    example_channel = _get_example_channel(config)
    
    return {
        "bot_id": bot_id,
        "bot_name": bot_config.get('name', bot_id),
        "bot_title": bot_config.get('title', ''),
        "bot_user_id": my_user_id,
        "bot_role_id": my_role_id,
        "bot_description": persona.get('description', ''),
        "bot_personality": persona.get('personality', ''),
        "bot_speech_style": persona.get('speech_style', ''),
        "organization_name": config.organization.get('name', '组织'),
        "other_bots_info": other_bots_info,
        "channels_info": channels_info,
        "role_mention_map": role_mention_map,
        "user_mention_map": user_mention_map,
        "bot_keywords": "擅长领域: " + ", ".join(persona.get('keywords', [])),
        "bot_responsibilities": "职责范围: " + ", ".join(persona.get('responsibilities', [])),
        "example_other_role_id": example_other.get('role_id', 'ROLE_ID'),
        "example_channel_name": example_channel.get('name', '频道'),
        "context": "{context}",  # Runtime replacement
    }


def _build_other_bots_info(my_bot_id: str, config: MultiBotConfig) -> str:
    """Build information list of other bots."""
    info_lines = []
    
    for other_id, other_config in config.bots.items():
        if other_id != my_bot_id:
            user_id = config.get_user_id_for_bot(other_id) or "N/A"
            role_id = config.get_role_id_for_bot(other_id) or "N/A"
            persona = other_config.get('persona', {})
            
            info_lines.append(
                f"- **{other_config.get('name')}** ({other_config.get('title')})\n"
                f"  - Bot ID: `{other_id}`\n"
                f"  - 用户ID: `{user_id}`\n"
                f"  - 角色ID: `{role_id}`\n"
                f"  - 职责: {persona.get('description', '')}"
            )
    
    return "\n\n".join(info_lines) if info_lines else "(无其他 Bot)"


def _build_channels_info(config: MultiBotConfig) -> str:
    """Build channel information list."""
    info_lines = []
    
    for channel_name, channel_config in config.channels.items():
        info_lines.append(
            f"- **{channel_config.get('name')}** (`{channel_name}`)\n"
            f"  - 频道ID: `{channel_config.get('id')}`\n"
            f"  - 描述: {channel_config.get('description', '')}\n"
            f"  - 可用Bot: {', '.join(channel_config.get('allowed_bots', []))}"
        )
    
    return "\n\n".join(info_lines)


def _build_mention_maps(config: MultiBotConfig) -> tuple:
    """Build mention maps."""
    role_lines = []
    user_lines = []
    
    for bot_id in config.bots.keys():
        bot_config = config.get_bot_config(bot_id)
        name = bot_config.get('name', bot_id)
        
        role_id = config.get_role_id_for_bot(bot_id)
        user_id = config.get_user_id_for_bot(bot_id)
        
        if role_id:
            role_lines.append(f"- {name}: `<@&{role_id}>`")
        
        if user_id:
            user_lines.append(f"- {name}: `<@{user_id}>`")
    
    return "\n".join(role_lines), "\n".join(user_lines)


def _get_example_other_bot(my_bot_id: str, config: MultiBotConfig) -> Dict:
    """Get another bot as example."""
    for bot_id in config.bots.keys():
        if bot_id != my_bot_id:
            return {
                'bot_id': bot_id,
                'role_id': config.get_role_id_for_bot(bot_id) or 'ROLE_ID',
                'name': config.get_bot_config(bot_id).get('name', bot_id)
            }
    return {'role_id': 'ROLE_ID', 'name': '其他Bot'}


def _get_example_channel(config: MultiBotConfig) -> Dict:
    """Get a channel as example."""
    for channel_name, channel_config in config.channels.items():
        return {
            'name': channel_config.get('name', channel_name),
            'id': channel_config.get('id', 'CHANNEL_ID')
        }
    return {'name': '频道', 'id': 'CHANNEL_ID'}


def format_system_prompt(bot_id: str, config: MultiBotConfig, context: str = "") -> str:
    """
    Format System Prompt.
    
    Args:
        bot_id: Bot ID
        config: Configuration object
        context: Current conversation context
        
    Returns:
        Complete System Prompt
    """
    arch_info = build_system_architecture_info(bot_id, config)
    arch_info["context"] = context if context else "(无上下文)"
    
    return SYSTEM_PROMPT_TEMPLATE.format(**arch_info)


def parse_mentions_from_content(content: str, config: MultiBotConfig) -> List[str]:
    """
    Parse @ mentions from message content.
    
    Args:
        content: Message content
        config: Configuration object
        
    Returns:
        List of bot_ids
    """
    mentions = []
    
    # Match <@&role_id>
    role_pattern = r'<@&(\d+)>'
    for match in re.finditer(role_pattern, content):
        role_id = match.group(1)
        bot_id = config.get_bot_id_from_role_id(role_id)
        if bot_id:
            mentions.append(bot_id)
    
    # Match <@user_id>
    user_pattern = r'<@(\d+)>'
    for match in re.finditer(user_pattern, content):
        user_id = match.group(1)
        bot_id = config.get_bot_id_from_user_id(user_id)
        if bot_id:
            mentions.append(bot_id)
    
    return mentions


def resolve_channel_name(text: str, config: MultiBotConfig) -> Optional[str]:
    """
    Resolve channel name from text.
    
    Args:
        text: User input text
        config: Configuration object
        
    Returns:
        Channel config key, or None
    """
    # Match aliases
    for alias, channel_key in CHANNEL_NAME_ALIASES.items():
        if alias in text:
            return channel_key
    
    return None


def get_channel_id_from_text(text: str, config: MultiBotConfig) -> Optional[str]:
    """
    Get channel ID from text.
    
    Args:
        text: User input text
        config: Configuration object
        
    Returns:
        Channel ID, or None
    """
    channel_key = resolve_channel_name(text, config)
    if channel_key:
        return config.resolve_channel_id(channel_key)
    return None
