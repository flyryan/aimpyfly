"""
AIM message handler for the AIM chatbot.
Handles AIM connection and message processing.
"""
import asyncio
from typing import Dict, Any, Callable, Coroutine, Optional
from aimpyfly import aim_client

from aimbot.utils.logger import get_logger

logger = get_logger(__name__)

class AIMHandler:
    """
    Handler for AIM connection and message processing.
    
    Attributes:
        client (aim_client.AIMClient): AIM client
        message_callback (Callable): Callback function for message handling
    """
    
    def __init__(self, credentials: Dict[str, Any], message_callback: Callable[[str, str], Coroutine[Any, Any, None]]):
        """
        Initialize the AIM handler.
        
        Args:
            credentials (Dict[str, Any]): AIM credentials (username, password, server, port)
            message_callback (Callable): Callback function for message handling
        """
        self.credentials = credentials
        self.message_callback = message_callback
        self.client = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        logger.debug(f"Initialized AIM handler for user {credentials['username']}")
    
    async def _on_message_received(self, sender: str, message: str):
        """
        Callback for handling incoming AIM messages.
        
        Args:
            sender (str): Sender's username
            message (str): Message content
        """
        logger.info(f"Received message from {sender}: {message}")
        await self.message_callback(sender, message)
    
    async def connect(self) -> bool:
        """
        Connect to the AIM server.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            # Initialize the AIM client
            self.client = aim_client.AIMClient(
                server=self.credentials['server'],
                port=self.credentials['port'],
                username=self.credentials['username'],
                password=self.credentials['password'],
                loglevel=logger.level
            )
            
            # Set the message callback
            self.client.set_message_callback(self._on_message_received)
            
            # Connect to the AIM server
            logger.info(f"Connecting to AIM server {self.credentials['server']}:{self.credentials['port']} as {self.credentials['username']}")
            await self.client.connect()
            
            self.connected = True
            self.reconnect_attempts = 0
            logger.info(f"Connected to AIM server as {self.credentials['username']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to AIM server: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from the AIM server."""
        if self.client:
            try:
                # AIMPyfly doesn't have a disconnect method, so we'll just set the flag
                self.connected = False
                logger.info("Disconnected from AIM server")
            except Exception as e:
                logger.error(f"Error disconnecting from AIM server: {str(e)}")
    
    async def send_message(self, recipient: str, message: str) -> bool:
        """
        Send a message to an AIM user.
        
        Args:
            recipient (str): Recipient's username
            message (str): Message content
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.client or not self.connected:
            logger.error("Cannot send message: Not connected to AIM server")
            return False
        
        try:
            logger.info(f"Sending message to {recipient}")
            await self.client.send_message(recipient, message)
            logger.debug(f"Message sent to {recipient}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {recipient}: {str(e)}")
            return False
    
    async def handle_disconnect(self):
        """Handle disconnection from the AIM server."""
        self.connected = False
        
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            reconnect_delay = self.reconnect_delay * self.reconnect_attempts
            
            logger.warning(f"Disconnected from AIM server. Attempting to reconnect in {reconnect_delay} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
            
            await asyncio.sleep(reconnect_delay)
            success = await self.connect()
            
            if success:
                logger.info("Successfully reconnected to AIM server")
            else:
                await self.handle_disconnect()
        else:
            logger.error(f"Failed to reconnect to AIM server after {self.max_reconnect_attempts} attempts")
    
    async def process_incoming_packets(self):
        """Process incoming AIM packets."""
        if not self.client or not self.connected:
            logger.error("Cannot process packets: Not connected to AIM server")
            return
        
        try:
            logger.info("Starting to process incoming AIM packets")
            await self.client.process_incoming_packets()
        except Exception as e:
            logger.error(f"Error processing incoming packets: {str(e)}")
            await self.handle_disconnect()
