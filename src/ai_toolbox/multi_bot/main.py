"""Main entry point for Cyber Dynasty Multi-Bot System."""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from .hub_listener import HubListener, discord_message_to_unified
from .message_bus import MessageBus
from .role_bot import RoleBot
from .config import DYNASTY_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    
    # Verify required environment variables
    required_vars = [
        "HUB_BOT_TOKEN",
        "CHENGXIANG_BOT_TOKEN",
        "TAIWEI_BOT_TOKEN",
        "KIMI_API_KEY"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        sys.exit(1)
    
    logger.info("All required environment variables found")
    
    # Initialize Message Bus
    bus = MessageBus()
    
    # Create and register bots
    for bot_id, config in DYNASTY_CONFIG.bots.items():
        try:
            bot = RoleBot(config)
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
    bus.set_debug_sender(hub.send_debug_message)
    for bot in bus.role_bots.values():
        bot.set_debug_sender(hub.send_debug_message)
    
    # Start system
    logger.info("Starting Cyber Dynasty Multi-Bot System...")
    
    try:
        await hub.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        # Cleanup
        logger.info("Shutting down...")
        await hub.stop()
        for bot in bus.role_bots.values():
            await bot.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
