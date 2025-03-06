"""
Main bot class for the AIM chatbot.
Integrates AIM and Dify API functionality.
"""
import asyncio
import uuid
from typing import Dict, Any, Optional

from aimbot.api.dify_client import DifyClient
from aimbot.bot.aim_handler import AIMHandler
from aimbot.utils.logger import get_logger

logger = get_logger(__name__)

class AIMBot:
    """
    Main bot class that integrates AIM and Dify API functionality.
    
    Attributes:
        aim_handler (AIMHandler): Handler for AIM connection and messages
        dify_client (DifyClient): Client for Dify API
        user_sessions (Dict[str, str]): Map of AIM usernames to session IDs
    """
    
    def __init__(self, aim_credentials: Dict[str, Any], dify_client: DifyClient):
        """
        Initialize the AIM bot.
        
        Args:
            aim_credentials (Dict[str, Any]): AIM credentials
            dify_client (DifyClient): Dify API client
        """
        self.dify_client = dify_client
        self.aim_handler = AIMHandler(aim_credentials, self.handle_message)
        self.user_sessions: Dict[str, str] = {}  # Map AIM usernames to session IDs
        self.running = False
        
        logger.debug("Initialized AIM bot")
    
    async def start(self):
        """Start the bot."""
        logger.info("Starting AIM bot")
        self.running = True
        
        # Connect to AIM
        connected = await self.aim_handler.connect()
        if not connected:
            logger.error("Failed to connect to AIM. Bot cannot start.")
            self.running = False
            return False
        
        # Start processing incoming packets
        logger.info("AIM bot started successfully")
        return True
    
    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping AIM bot")
        self.running = False
        
        # Disconnect from AIM
        await self.aim_handler.disconnect()
        
        # Close Dify client session
        await self.dify_client.close()
        
        logger.info("AIM bot stopped")
    
    async def handle_message(self, sender: str, message: str):
        """
        Handle an incoming message from AIM.
        
        Args:
            sender (str): Sender's username
            message (str): Message content
        """
        try:
            logger.info(f"Processing message from {sender}")
            
            # Get or create a session ID for this user
            session_id = self.user_sessions.get(sender)
            if not session_id:
                session_id = str(uuid.uuid4())
                self.user_sessions[sender] = session_id
                logger.debug(f"Created new session for {sender}: {session_id}")
            
            # Send typing notification
            await self.aim_handler.send_typing_notification(sender, True)
            
            # Create a task for sending periodic typing notifications
            typing_task = asyncio.create_task(self._send_periodic_typing(sender))
            
            try:
                # Send the message to Dify API
                response_text, metadata = await self.dify_client.send_message(session_id, message)
                
                # Cancel the typing notification task
                typing_task.cancel()
                
                # Send "stopped typing" notification
                await self.aim_handler.send_typing_notification(sender, False)
                
                # Send the response back to the AIM user
                await self.send_response(sender, response_text)
                
            except asyncio.CancelledError:
                logger.warning(f"Message processing for {sender} was cancelled")
                await self.aim_handler.send_typing_notification(sender, False)
            finally:
                # Ensure typing task is cancelled
                if not typing_task.done():
                    typing_task.cancel()
            
        except Exception as e:
            logger.error(f"Error handling message from {sender}: {str(e)}")
            await self.handle_error(sender, str(e))
    
    async def _send_periodic_typing(self, recipient: str, interval: float = 5.0):
        """
        Send periodic typing notifications to keep the typing indicator active.
        
        Args:
            recipient (str): Recipient's username
            interval (float): Interval between typing notifications in seconds
        """
        try:
            while True:
                await asyncio.sleep(interval)
                await self.aim_handler.send_typing_notification(recipient, True)
                logger.debug(f"Sent periodic typing notification to {recipient}")
        except asyncio.CancelledError:
            logger.debug(f"Periodic typing notifications to {recipient} cancelled")
            raise
    
    async def send_response(self, recipient: str, response: str):
        """
        Send a response to an AIM user.
        
        Args:
            recipient (str): Recipient's username
            response (str): Response content
        """
        # Check if the response is too long for AIM
        # AIM has a message size limit, so we might need to split long messages
        max_message_length = 2000  # AIM message size limit
        
        if len(response) <= max_message_length:
            # Send the response as a single message
            await self.aim_handler.send_message(recipient, response)
        else:
            # Split the response into multiple messages
            chunks = [response[i:i+max_message_length] for i in range(0, len(response), max_message_length)]
            
            for i, chunk in enumerate(chunks):
                # Add a prefix to indicate that this is a multi-part message
                prefix = f"[{i+1}/{len(chunks)}] "
                await self.aim_handler.send_message(recipient, prefix + chunk)
                
                # Add a small delay between messages to avoid flooding
                await asyncio.sleep(0.5)
    
    async def handle_error(self, recipient: str, error: str):
        """
        Handle an error by sending an error message to the user.
        
        Args:
            recipient (str): Recipient's username
            error (str): Error message
        """
        error_message = f"Sorry, I encountered an error: {error}"
        await self.aim_handler.send_message(recipient, error_message)
    
    async def run(self):
        """Run the bot's main loop."""
        if not self.running:
            success = await self.start()
            if not success:
                return
        
        try:
            logger.info("Starting main bot loop")
            await self.aim_handler.process_incoming_packets()
        except KeyboardInterrupt:
            logger.info("Bot interrupted by user")
        except Exception as e:
            logger.error(f"Error in bot main loop: {str(e)}")
        finally:
            await self.stop()
