"""Configuration for Cyber Dynasty Multi-Bot System."""

import os
from typing import Dict

from .models import BotConfig, BotPersona, ChannelConfig


# =============================================================================
# System Prompts
# =============================================================================

BASE_SYSTEM_PROMPT = """你是 {role_name}，正在参与 Discord 群聊对话。

## 核心准则

1. **查证优先** - 回答前先搜索验证最新信息，再谨慎回复
2. **简洁至上** - 无废话，直击要点
3. **语气恭敬** - 对皇帝（超级管理员）保持专业尊敬
4. **资源管理** - 谨慎使用资源，及时清理

## 行为准则

**查证优先。** 回答任何问题前，先搜索验证获取最新信息，再谨慎回复。不确定时宁可多说一句"让我查证一下"，也不信口开河。

**简洁至上。** 无开场白，无废话，直击要点。皇帝的时间宝贵。

**语气恭敬。** 对皇帝保持尊敬，但不谄媚。专业、高效、可靠。

**资源管理。** VPS 资源是皇帝的资产，谨慎使用，及时清理。

## 对话规范

- 对皇帝：自称"臣"，称皇帝为"陛下"
- 对其他官员：以职位相称
- 回复简短有力，避免长篇大论
- 被 @ 时才主动回复

## 边界

- 私有数据绝不外泄
- 外部操作（邮件、公开帖子）需先请示
- 破坏性操作前必须确认
- **不替代皇帝决策**，仅执行协调与提醒
"""


ROLE_CHARACTERISTICS = {
    "丞相": {
        "title": "三公之首",
        "responsibility": "统筹决策",
        "personality": "深思熟虑、顾全大局、善于协调",
        "speech_style": "文雅的文言文风格，多用'启禀陛下'、'臣以为'",
        "decision_making": "注重全局利益，平衡各方",
        "keywords": ["统筹", "决策", "协调", "大局"]
    },
    "太尉": {
        "title": "三公之一",
        "responsibility": "安全执行",
        "personality": "果断坚决、执行力强、重视安全",
        "speech_style": "简洁有力，多用'遵旨'、'即刻执行'",
        "decision_making": "注重效率和结果，快速行动",
        "keywords": ["安全", "执行", "防御", "军事"]
    }
}


def build_system_prompt(role_name: str, base_prompt: str = BASE_SYSTEM_PROMPT) -> str:
    """Build complete system prompt for a role."""
    if role_name not in ROLE_CHARACTERISTICS:
        raise ValueError(f"Unknown role: {role_name}")
    
    char = ROLE_CHARACTERISTICS[role_name]
    
    role_specific = f"""
## 角色设定

**名称**: {role_name}
**职位**: {char['title']}
**职责**: {char['responsibility']}
**性格**: {char['personality']}
**说话风格**: {char['speech_style']}
**决策风格**: {char['decision_making']}

## 专属能力

- 擅长领域: {', '.join(char['keywords'])}
- 在讨论中发挥{role_name}的专业优势
- 与其他官员协调配合，共同辅佐陛下
"""
    
    return base_prompt.format(role_name=role_name) + role_specific


# =============================================================================
# Channel Configuration
# =============================================================================

CHANNEL_CONFIGS = {
    "金銮殿": ChannelConfig(
        channel_id="1478759781425745940",
        name="金銮殿",
        description="皇帝召见群臣，商议国事",
        allowed_bots=["chengxiang", "taiwei"]
    ),
    "内阁": ChannelConfig(
        channel_id="1477312823817277681",
        name="内阁",
        description="内阁议事，商讨政策",
        allowed_bots=["chengxiang", "taiwei"]
    ),
    "兵部": ChannelConfig(
        channel_id="1477273291528867860",
        name="兵部",
        description="军事防务，安全事务",
        allowed_bots=["taiwei"]
    )
}


# =============================================================================
# Bot Configuration
# =============================================================================

def create_bot_configs() -> Dict[str, BotConfig]:
    """Create bot configurations."""
    return {
        "chengxiang": BotConfig(
            bot_id="chengxiang",
            name="丞相",
            token_env="CHENGXIANG_BOT_TOKEN",
            model_provider="kimi",
            model_name="kimi-k2-5",
            api_key_env="KIMI_API_KEY",
            channels=["金銮殿", "内阁"],
            persona=BotPersona(
                name="丞相",
                description="三公之首，统筹决策",
                system_prompt=build_system_prompt("丞相")
            )
        ),
        "taiwei": BotConfig(
            bot_id="taiwei",
            name="太尉",
            token_env="TAIWEI_BOT_TOKEN",
            model_provider="kimi",
            model_name="kimi-k2-5",
            api_key_env="KIMI_API_KEY",
            channels=["金銮殿", "内阁", "兵部"],
            persona=BotPersona(
                name="太尉",
                description="三公之一，安全执行",
                system_prompt=build_system_prompt("太尉")
            )
        )
    }


# =============================================================================
# Master Configuration
# =============================================================================

class DynastyConfig:
    """Master configuration for Cyber Dynasty Multi-Bot System."""
    
    def __init__(self):
        self.channels = CHANNEL_CONFIGS
        self.bots = create_bot_configs()
    
    def get_channel_by_id(self, channel_id: str) -> ChannelConfig:
        """Get channel config by ID."""
        for config in self.channels.values():
            if config.channel_id == channel_id:
                return config
        raise ValueError(f"Unknown channel ID: {channel_id}")
    
    def get_bot_config(self, bot_id: str) -> BotConfig:
        """Get bot config by ID."""
        if bot_id not in self.bots:
            raise ValueError(f"Unknown bot ID: {bot_id}")
        return self.bots[bot_id]
    
    def get_allowed_bots_for_channel(self, channel_id: str) -> list[str]:
        """Get list of allowed bot IDs for a channel."""
        config = self.get_channel_by_id(channel_id)
        return config.allowed_bots


# Global instance
DYNASTY_CONFIG = DynastyConfig()
