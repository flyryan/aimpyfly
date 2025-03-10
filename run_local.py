#!/usr/bin/env python3
"""
Script to run the AIM bot locally with streaming mode enabled.
This allows for easier debugging and monitoring of the bot's behavior.
"""
import asyncio
import os
import logging
import sys

# Set environment variables for local testing
os.environ["AIM_USERNAME"] = "accountnamer"  # Replace with your AIM username
os.environ["AIM_PASSWORD"] = "password123"  # Replace with your AIM password
os.environ["AIM_SERVER"] = "aim.visionfun.org"
os.environ["AIM_PORT"] = "5190"
os.environ["DIFY_API_KEY"] = "app-ONu0R9S3wESNtJyZRRjZKscX"  # Replace with your Dify API key
os.environ["DIFY_API_URL"] = "http://52.89.105.190/v1"
os.environ["API_MODE"] = "streaming"  # Set to streaming mode
os.environ["LOG_LEVEL"] = "DEBUG"  # Set to DEBUG for more verbose logging

# Configure logging to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Import the bot after setting environment variables
from aimbot.api.dify_client import DifyClient
from aimbot.bot.bot import AIMBot
from aimbot.config.settings import get_aim_credentials, get_dify_config

async def main():
    """Run the AIM bot locally."""
    try:
        print("Starting AIM bot locally with streaming mode...")
        print(f"API Mode: {os.environ['API_MODE']}")
        
        # Load configuration
        aim_credentials = get_aim_credentials()
        dify_config = get_dify_config()
        
        print(f"AIM Credentials: {aim_credentials['username']}@{aim_credentials['server']}:{aim_credentials['port']}")
        print(f"Dify Config: URL={dify_config['api_url']}, Mode={dify_config['mode']}")
        
        # Initialize Dify client
        dify_client = DifyClient(
            api_key=dify_config['api_key'],
            api_url=dify_config['api_url'],
            mode=dify_config['mode']
        )
        
        # Create and start bot
        bot = AIMBot(aim_credentials, dify_client)
        
        # Run the bot
        print("Running bot... Press Ctrl+C to stop")
        await bot.run()
        
    except KeyboardInterrupt:
        print("\nBot interrupted by user")
    except Exception as e:
        print(f"Error in main: {str(e)}")
        if 'bot' in locals():
            await bot.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())