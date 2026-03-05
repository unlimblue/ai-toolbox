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
from .architecture_builder import build_system_prompt, PromptBuilder
from .models import BotConfig, BotPersona

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_bot_from_config(bot_id: str, config: MultiBotConfig) -> RoleBot:
    """
    Create RoleBot instance from configuration with architecture awareness.
    
    Args:
        bot_id: Bot identifier
        config: MultiBotConfig instance
        
    Returns:
        RoleBot instance with full system architecture awareness
    """
    bot_config_dict = config.get_bot_config(bot_id)
    
    # Build system prompt with architecture awareness
    system_prompt = build_system_prompt(bot_id, config, context="")
    
    # Create BotConfig
    persona = BotPersona(
        name=bot_config_dict.get("name", bot_id),
        description=bot_config_dict.get("persona", {}).get("description", ""),
        system_prompt=system_prompt
    )
    
    bot_config = BotConfig(
        bot_id=bot_id,
        name=bot_config_dict.get("name", bot_id),
        token_env=f"{bot_id.upper()}_BOT_TOKEN",
        model_provider=bot_config_dict.get("model_provider", "kimi"),
        model_name=bot_config_dict.get("model_name", "kimi-k2-5"),
        api_key_env="KIMI_API_KEY",
        channels=bot_config_dict.get("channels", []),
        persona=persona
    )
    
    # Build architecture info for the bot
    architecture_info = {
        "bot_id": bot_id,
        "bot_name": bot_config_dict.get("name", bot_id),
        "bot_user_id": config.get_user_id_for_bot(bot_id),
        "bot_role_id": config.get_role_id_for_bot(bot_id),
    }
    
    return RoleBot(bot_config, architecture_info=architecture_info)


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
    
    # Create and register bots from configuration with architecture awareness
    for bot_id in config.bots.keys():
        try:
            bot = create_bot_from_config(bot_id, config)
            bus.register_bot(bot)
            logger.info(f"Created and registered bot with architecture awareness: {bot_id}")
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
