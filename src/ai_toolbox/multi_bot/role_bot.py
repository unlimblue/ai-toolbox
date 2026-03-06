"""Role Bot - Autonomous bot with full decision-making capability."""

import asyncio
import json
import logging
import os
import re
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime, timedelta

import discord

from ..providers import create_provider
from ..providers.base import ChatMessage
from .models import UnifiedMessage, BotState, BotConfig
from .config_loader import get_config

logger = logging.getLogger(__name__)


class RoleBot:
    """
    Autonomous Role Bot with full decision-making capability.
    
    Features:
    - Receives messages with context from ContextGraph
    - AI autonomously decides channel, mentions, and content
    - Executes multiple actions based on AI decisions
    - No hardcoded logic
    """
    
    def __init__(self, config: BotConfig, graph_manager=None):
        self.config = config
        self.bot_id = config.bot_id
        self.graph_manager = graph_manager
        self.state = BotState.IDLE
        
        # Discord client
        self._client: Optional[discord.Client] = None
        self._connected = False
        self.token = os.getenv(config.token_env)
        
        # Debug
        self.debug_sender: Optional[Callable] = None
    
    def set_debug_sender(self, sender: Callable):
        """Set debug message sender."""
        self.debug_sender = sender
    
    async def _send_debug(self, content: str, data: dict = None):
        """Send debug message."""
        if self.debug_sender:
            try:
                await self.debug_sender(f"[{self.bot_id}] {content}", data)
            except Exception as e:
                logger.error(f"Debug send error: {e}")
    
    async def connect(self):
        """Connect to Discord."""
        if self._connected or not self.token:
            return
        
        self._client = discord.Client(intents=discord.Intents.default())
        
        @self._client.event
        async def on_ready():
            logger.info(f"Bot {self.bot_id} logged in as {self._client.user}")
            await self._send_debug(f"🟢 Bot online: {self._client.user}")
        
        self._connected = True
        try:
            await self._client.start(self.token)
        except Exception as e:
            self._connected = False
            raise
    
    async def handle_message(self, message: UnifiedMessage, graph_id: str):
        """
        Handle incoming message with full autonomy.
        
        Flow:
        1. Get context from ContextGraph
        2. Build decision prompt
        3. AI decides actions (JSON format)
        4. Execute all actions
        """
        await self._send_debug(
            "📥 Handling message",
            {"message_id": message.id, "content": message.content[:50]}
        )
        
        # Skip own messages
        if self._is_own_message(message):
            await self._send_debug("⏭️ Skipping own message")
            return
        
        # 1. Get context from ContextGraph
        context_text = ""
        if self.graph_manager:
            try:
                subgraph = self.graph_manager.get_context_for_bot(
                    graph_id, self.bot_id, limit=15
                )
                if subgraph:
                    context_text = subgraph.get_linear_history()
                    await self._send_debug(
                        "📊 Got context from graph",
                        {"nodes": len(subgraph.nodes)}
                    )
            except Exception as e:
                logger.error(f"Error getting context: {e}")
        
        # 2. Build decision prompt
        decision_prompt = self._build_decision_prompt(message, context_text)
        
        # 3. AI decides
        try:
            actions = await self._ai_decide(decision_prompt)
            await self._send_debug(
                "🤖 AI decided actions",
                {"action_count": len(actions)}
            )
        except Exception as e:
            logger.error(f"AI decision error: {e}")
            # Fallback: simple acknowledgment
            await self._send_debug("⚠️ AI decision failed, using fallback")
            await self.send_message(
                message.channel_id,
                "臣已收到。"
            )
            return
        
        # 4. Execute actions
        for i, action in enumerate(actions):
            try:
                channel_id = action.get("channel_id")
                content = action.get("content", "").strip()
                
                if channel_id and content:
                    await self._send_debug(
                        f"📤 Executing action {i+1}/{len(actions)}",
                        {"channel": channel_id, "content": content[:50]}
                    )
                    await self.send_message(channel_id, content)
                    
                    # Small delay between multiple actions
                    if len(actions) > 1 and i < len(actions) - 1:
                        await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Action execution error: {e}")
    
    def _is_own_message(self, message: UnifiedMessage) -> bool:
        """Check if message is from this bot."""
        # Check by ID
        if message.author_id == self.bot_id:
            return True
        
        # Check by name
        if self.config.persona and message.author_name == self.config.persona.name:
            return True
        
        return False
    
    def _build_decision_prompt(self, message: UnifiedMessage, 
                               context_text: str) -> str:
        """Build prompt for AI decision-making."""
        # Get available channels
        channels_info = self._get_available_channels_info()
        
        # Get other bots info
        other_bots_info = self._get_other_bots_info()
        
        prompt = f"""你收到了一条消息，需要自主决定如何响应。

## 你的身份
- 名称: {self.config.persona.name if self.config.persona else self.bot_id}
- 描述: {self.config.persona.description if self.config.persona else ''}

## 收到的消息
来自: {message.author_name}
内容: {message.content}
当前频道: {message.channel_id}

## 对话上下文
{context_text if context_text else "(无历史上下文)"}

## 可用频道
{channels_info}

## 协作对象
{other_bots_info}

## 决策指南

你需要自主决定: 在哪里说什么（可以包括 @ 谁）。

**场景示例**:
- 用户说"去内阁通知太尉" → 你应该在内阁 @太尉
- 用户说"来金銮殿回话" → 你应该在金銮殿回复  
- 用户说"通知太尉来金銮殿" → 在内阁 @太尉，然后回金銮殿汇报

**@ 格式**:
- 使用 `\u003c@\u0026ROLE_ID\u003e` 格式 @ 其他 Bot

## 输出格式

用 JSON 格式输出你的行动计划:

```json
{{
  "actions": [
    {{
      "channel_id": "频道ID",
      "content": "消息内容（可以包含 @）",
      "reason": "简要说明"
    }}
  ],
  "plan": "整体计划简述"
}}
```

如果不需响应，返回空数组。如果只有一个动作，数组只有一个元素。"""
        
        return prompt
    
    def _get_available_channels_info(self) -> str:
        """Get formatted channel info."""
        try:
            config = get_config()
            channels = []
            for key, ch in config.channels.items():
                channels.append(f"- {ch.get('name', key)} ({key}): ID {ch.get('id', 'N/A')}")
            return "\n".join(channels)
        except:
            return "- 金銮殿 (jinluan)\n- 内阁 (neige)\n- 兵部 (bingbu)"
    
    def _get_other_bots_info(self) -> str:
        """Get other bots info."""
        try:
            config = get_config()
            bots = []
            for bot_id, bot_config in config.bots.items():
                if bot_id != self.bot_id:
                    name = bot_config.get('name', bot_id)
                    role_id = config.get_role_id_for_bot(bot_id)
                    bots.append(f"- {name}: `\u003c@\u0026{role_id}\u003e`")
            return "\n".join(bots) if bots else "无其他协作 Bot"
        except:
            return "- 其他 Bot 信息暂不可用"
    
    async def _ai_decide(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Call AI to decide actions.
        
        Returns list of actions in format:
        [{"channel_id": "xxx", "content": "xxx", "reason": "xxx"}]
        """
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found: {self.config.api_key_env}")
        
        client = create_provider(
            self.config.model_provider,
            api_key=api_key,
            model=self.config.model_name
        )
        
        messages = [
            ChatMessage(role="system", 
                       content=self.config.persona.system_prompt if self.config.persona else ""),
            ChatMessage(role="user", content=prompt)
        ]
        
        response = await client.chat(messages)
        content = response.content.strip()
        
        # Parse JSON
        try:
            # Extract JSON from markdown code block if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            data = json.loads(content)
            actions = data.get("actions", [])
            
            # Validate actions
            valid_actions = []
            for action in actions:
                if isinstance(action, dict) and action.get("channel_id") and action.get("content"):
                    valid_actions.append(action)
            
            return valid_actions
        except json.JSONDecodeError:
            # If not valid JSON, treat as single action to current channel
            logger.warning(f"AI response not valid JSON: {content[:100]}")
            # Try to extract content
            return [{"channel_id": "current", "content": content, "reason": "Fallback"}]
    
    async def send_message(self, channel_id: str, content: str):
        """Send message to a channel."""
        # Convert [AT] markers to Discord mention format
        content = self._convert_at_markers(content)
        
        if not self._connected:
            await self.connect()
        
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                await channel.send(content)
                logger.info(f"Bot {self.bot_id} sent message to {channel_id}")
            else:
                logger.error(f"Channel not found: {channel_id}")
        except Exception as e:
            logger.error(f"Send message error: {e}")
    
    def _convert_at_markers(self, content: str) -> str:
        """
        Convert [AT] markers to Discord mention format.
        
        [AT]丞相 -> <@&14777314769764614239>
        [AT]太尉 -> <@&1478217215936430092>
        """
        # Get config for role IDs
        try:
            from .config_loader import get_config
            config = get_config()
            
            # Replace [AT]丞相 with role mention
            chengxiang_role = config.get_role_id_for_bot("chengxiang")
            if chengxiang_role and "[AT]丞相" in content:
                content = content.replace("[AT]丞相", f"<@&{chengxiang_role}>")
            
            # Replace [AT]太尉 with role mention
            taiwei_role = config.get_role_id_for_bot("taiwei")
            if taiwei_role and "[AT]太尉" in content:
                content = content.replace("[AT]太尉", f"<@&{taiwei_role}>")
            
            # Also handle generic [AT] fallback (should not happen with proper config)
            if "[AT]" in content:
                logger.warning(f"Unconverted [AT] marker found in: {content[:100]}")
                content = content.replace("[AT]", "@")  # Fallback to plain @
                
        except Exception as e:
            logger.error(f"Error converting AT markers: {e}")
            # Fallback: replace with plain @
            content = content.replace("[AT]", "@")
        
        return content
