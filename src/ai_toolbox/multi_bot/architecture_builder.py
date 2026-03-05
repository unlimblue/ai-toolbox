"""System architecture builder for Multi-Bot System."""

from typing import Dict, List
import re

from .config_loader import MultiBotConfig


# Enhanced System Prompt Template with Architecture Awareness
SYSTEM_PROMPT_TEMPLATE = """你是 {bot_name}（{bot_title}），在 {organization_name} 中担任重要角色。

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

## 👥 系统成员（你可以 @ 的人）

{other_bots_info}

## 📍 可用频道（你可以发言的地方）

{channels_info}

## 💬 如何正确 @ 人

当你想 @ 某人时，必须使用以下格式：

### 方法1: 使用角色 @（推荐）
格式: `<@&角色ID>`

可用角色映射:
{role_mention_map}

### 方法2: 使用用户 @
格式: `<@用户ID>`

可用用户映射:
{user_mention_map}

### 方法3: 使用名称（不推荐）
如果上述ID不可用，可以使用 `@名称`，但可能无法正确路由。

## 🎯 响应格式指南

当你需要响应并 @ 某人时，请使用以下格式：

**示例1 - 使用角色 @**:
```
<@&{example_other_role_id}>，我们去{example_channel_name}商议此事如何？
```

**示例2 - 确认指令**:
```
领旨，我这就去{example_channel_name}部署。
```

**示例3 - 多人讨论**:
```
<@&{example_other_role_id}>，我们去{example_channel_name}商议。
```

## 🏃 行动指南

当收到指令时，你需要：

1. **理解意图**: 分析说话人想要什么
2. **识别目标**: 确定需要 @ 谁（从系统成员中选择）
3. **选择频道**: 确定在哪个频道响应（从可用频道中选择）
4. **格式化 @**: 使用 `<@&角色ID>` 或 `<@用户ID>` 格式
5. **生成回复**: 结合以上信息生成完整回复

## 📋 当前对话上下文

{context}

## ⚠️ 重要提醒

- 必须正确使用 `<@&角色ID>` 或 `<@用户ID>` 格式，否则消息无法被正确路由
- 频道名称是给人看的，实际发送时需要使用频道ID（系统会自动处理）
- 你可以在任何可用频道发言，不限于当前频道

## 🎭 你的角色特性

{bot_keywords}
{bot_responsibilities}

请根据以上信息，自主决定如何响应。
"""


def build_system_architecture_info(bot_id: str, config: MultiBotConfig) -> Dict:
    """
    构建 Bot 的系统架构感知信息
    
    Args:
        bot_id: 当前 Bot 的 ID
        config: 配置对象
        
    Returns:
        用于填充 System Prompt 的字典
    """
    bot_config = config.get_bot_config(bot_id)
    persona = bot_config.get("persona", {})
    
    # 1. 构建其他 Bot 信息
    other_bots_info = _build_other_bots_info(bot_id, config)
    
    # 2. 构建频道信息
    channels_info = _build_channels_info(config)
    
    # 3. 构建 @ 映射表
    role_mention_map, user_mention_map = _build_mention_maps(config)
    
    # 4. 获取当前 Bot 的 ID 信息
    my_user_id = config.get_user_id_for_bot(bot_id) or "N/A"
    my_role_id = config.get_role_id_for_bot(bot_id) or "N/A"
    
    # 5. 获取示例数据（用于示例展示）
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
        "context": "{context}",  # 运行时替换
    }


def _build_other_bots_info(my_bot_id: str, config: MultiBotConfig) -> str:
    """构建其他 Bot 的信息列表"""
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
    
    return "\n\n".join(info_lines) if info_lines else "（无其他 Bot）"


def _build_channels_info(config: MultiBotConfig) -> str:
    """构建频道信息列表"""
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
    """构建 @ 映射表"""
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
    """获取一个其他 Bot 作为示例"""
    for bot_id in config.bots.keys():
        if bot_id != my_bot_id:
            return {
                'bot_id': bot_id,
                'role_id': config.get_role_id_for_bot(bot_id) or 'ROLE_ID',
                'name': config.get_bot_config(bot_id).get('name', bot_id)
            }
    return {'role_id': 'ROLE_ID', 'name': '其他Bot'}


def _get_example_channel(config: MultiBotConfig) -> Dict:
    """获取一个频道作为示例"""
    for channel_name, channel_config in config.channels.items():
        return {
            'name': channel_config.get('name', channel_name),
            'id': channel_config.get('id', 'CHANNEL_ID')
        }
    return {'name': '频道', 'id': 'CHANNEL_ID'}


def format_system_prompt(bot_id: str, config: MultiBotConfig, context: str = "") -> str:
    """
    格式化 System Prompt
    
    Args:
        bot_id: Bot ID
        config: 配置对象
        context: 当前对话上下文
        
    Returns:
        完整的 System Prompt
    """
    arch_info = build_system_architecture_info(bot_id, config)
    arch_info["context"] = context if context else "（无上下文）"
    
    return SYSTEM_PROMPT_TEMPLATE.format(**arch_info)


def parse_mentions_from_content(content: str, config: MultiBotConfig) -> List[str]:
    """
    从消息内容中解析 @ 提及
    
    Args:
        content: 消息内容
        config: 配置对象
        
    Returns:
        解析出的 bot_id 列表
    """
    mentions = []
    
    # 匹配 <@&role_id>
    role_pattern = r'<@&(\d+)>'
    for match in re.finditer(role_pattern, content):
        role_id = match.group(1)
        bot_id = config.get_bot_id_from_role_id(role_id)
        if bot_id:
            mentions.append(bot_id)
    
    # 匹配 <@user_id>
    user_pattern = r'<@(\d+)>'
    for match in re.finditer(user_pattern, content):
        user_id = match.group(1)
        bot_id = config.get_bot_id_from_user_id(user_id)
        if bot_id:
            mentions.append(bot_id)
    
    return mentions
