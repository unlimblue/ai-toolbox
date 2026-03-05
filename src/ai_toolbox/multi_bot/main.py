"""Main entry point for Cyber Dynasty Multi-Bot System."""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from .hub_listener import HubListener, discord_message_to_unified
from .message_bus import MessageBus
from .role_bot import RoleBot
from .config_loader import MultiBotConfig, get_config
from .models import BotConfig, BotPersona

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_bot_from_config(bot_id: str, config: MultiBotConfig) -> RoleBot:
    """
    Create RoleBot instance from configuration.
    
    Args:
        bot_id: Bot identifier
        config: MultiBotConfig instance
        
    Returns:
        RoleBot instance
    """
    bot_config_dict = config.get_bot_config(bot_id)
    
    # Create BotConfig from dictionary
    persona_dict = bot_config_dict.get("persona", {})
    persona = BotPersona(
        name=bot_config_dict.get("name", bot_id),
        description=persona_dict.get("description", ""),
        system_prompt=build_system_prompt_from_config(bot_id, config)
    )
    
    bot_config = BotConfig(
        bot_id=bot_id,
        name=bot_config_dict.get("name", bot_id),
        token_env=f"{bot_id.upper()}_BOT_TOKEN",
        model_provider=bot_config_dict.get("model_provider", "kimi"),
        model_name=bot_config_dict.get("model_name", "kimi-k2-5"),
        api_key_env=bot_config_dict.get("api_key", "KIMI_API_KEY").replace("${", "").replace("}", ""),
        channels=bot_config_dict.get("channels", []),
        persona=persona
    )
    
    return RoleBot(bot_config)


def build_system_prompt_from_config(bot_id: str, config: MultiBotConfig) -> str:
    """Build system prompt from configuration."""
    bot_config = config.get_bot_config(bot_id)
    persona = bot_config.get("persona", {})
    
    base_prompt = f"""你是 {bot_config.get('name', bot_id)}（{bot_config.get('title', '')}），正在参与 Discord 群聊对话。

## 角色设定

**名称**: {bot_config.get('name', bot_id)}
**职位**: {bot_config.get('title', '')}
**职责**: {persona.get('description', '')}
**性格**: {persona.get('personality', '')}
**说话风格**: {persona.get('speech_style', '')}
**决策风格**: {persona.get('decision_making', '')}

## 能力

- 可以在任意频道发言
- 可以 @ 任何人（人类或其他 Bot）
- 根据情境自主决定行动

## 专属能力

- 擅长领域: {', '.join(persona.get('keywords', []))}
- 职责范围: {', '.join(persona.get('responsibilities', []))}
"""
    
    return base_prompt


async def main():
    """Main entry point."""
    # Load environment variables
    env_path = os.path.expanduser("~/.openclaw/secrets/cyber_dynasty_tokens.env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_path}")
    else:
        load_dotenv()
        logger.info("Loaded environment from default locations")
    
    # Load configuration
    config_path = os.getenv("MULTI_BOT_CONFIG", "config/multi_bot.yaml")
    try:
        config = get_config(config_path)
        logger.info(f"Loaded configuration from {config_path}")
        logger.info(f"Organization: {config.organization.get('name', 'Unknown')}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Verify required environment variables
    required_vars = ["HUB_BOT_TOKEN", "KIMI_API_KEY"]
    bot_ids = list(config.bots.keys())
    for bot_id in bot_ids:
        required_vars.append(f"{bot_id.upper()}_BOT_TOKEN")
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        sys.exit(1)
    
    logger.info("All required environment variables found")
    
    # Initialize Message Bus
    bus = MessageBus()
    
    # Create and register bots from configuration
    for bot_id in config.bots.keys():
        try:
            bot = create_bot_from_config(bot_id, config)
            bus.register_bot(bot)
            logger.info(f"Created and registered bot: {bot_id}")
        except Exception as e:
            logger.error(f"Failed to create bot {bot_id}: {e}")
    
    # Initialize Hub Listener
    async def on_discord_message(discord_msg):
        """Handle Discord message."""
        unified_msg = discord_message_to_unified(discord_msg)
        await bus.publish(unified_msg)
    
    hub = HubListener(
        token=os.getenv("HUB_BOT_TOKEN"),
        on_message=on_discord_message
    )
    
    # Connect debug sender after hub is initialized
    if config.is_debug_enabled():
        bus.set_debug_sender(hub.send_debug_message)
        for bot in bus.role_bots.values():
            bot.set_debug_sender(hub.send_debug_message)
        logger.info("Debug mode enabled")
    
    # Connect all bots at startup
    logger.info("Connecting all bots...")
    bot_tasks = []
    for bot_id, bot in bus.role_bots.items():
        try:
            task = asyncio.create_task(bot.connect())
            bot_tasks.append((bot_id, task))
            logger.info(f"Started connection task for bot: {bot_id}")
        except Exception as e:
            logger.error(f"Failed to start connection for bot {bot_id}: {e}")
    
    # Wait for bots to connect
    logger.info("Waiting for bots to connect...")
    await asyncio.sleep(3)
    
    # Check connection status
    connected_count = sum(1 for bot in bus.role_bots.values() if bot._connected)
    logger.info(f"Connected bots: {connected_count}/{len(bus.role_bots)}")
    
    # Start system
    logger.info(f"Starting {config.organization.get('name', 'Multi-Bot')} System...")
    
    try:
        await hub.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        # Cleanup
        logger.info("Shutting down...")
        
        # Cancel bot tasks
        for bot_id, task in bot_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        await hub.stop()
        for bot in bus.role_bots.values():
            await bot.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
