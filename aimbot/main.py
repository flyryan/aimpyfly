"""
Entry point for the AIM chatbot.
"""
import asyncio
import signal
import sys
from typing import Dict, Any

from aimbot.api.dify_client import DifyClient
from aimbot.bot.bot import AIMBot
from aimbot.config.settings import get_aim_credentials, get_dify_config, get_logging_config
from aimbot.utils.logger import get_logger

# Set up logger
logger = get_logger(__name__)

# Global variables
bot = None

async def main():
    """Main entry point for the AIM chatbot."""
    try:
        logger.info("Starting AIM chatbot")
        
        # Load configuration
        aim_credentials = get_aim_credentials()
        dify_config = get_dify_config()
        
        # Initialize Dify client
        logger.info(f"Initializing Dify client with API URL: {dify_config['api_url']}")
        dify_client = DifyClient(
            api_key=dify_config['api_key'],
            api_url=dify_config['api_url'],
            mode=dify_config['mode']
        )
        
        # Create and start bot
        global bot
        bot = AIMBot(aim_credentials, dify_client)
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        
        # Run the bot
        logger.info("Running bot")
        await bot.run()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        if bot:
            await bot.stop()
        sys.exit(1)

async def shutdown():
    """Shutdown the bot gracefully."""
    logger.info("Shutting down...")
    if bot:
        await bot.stop()
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)
