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
        self.message_buffers: Dict[str, Dict[str, Any]] = {}  # Message buffers for each user
        self.processing_users: Dict[str, bool] = {}  # Track users with ongoing API requests
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
            
            # Check if this is a "clear" command
            if message.strip().lower() == "clear":
                # Reset processing state
                self.processing_users[sender] = False
                
                await self._handle_clear_command(sender)
                return
            
            # Get or create a session ID for this user
            session_id = self.user_sessions.get(sender)
            if not session_id:
                session_id = str(uuid.uuid4())
                self.user_sessions[sender] = session_id
                logger.debug(f"Created new session for {sender}: {session_id}")
            
            # Check if we're already processing a message for this user
            if self.processing_users.get(sender, False):
                logger.info(f"User {sender} has a message being processed, buffering new message")
                await self._buffer_message(sender, message)
                return
            
            # Check if the message is very short (likely part of a multi-message input)
            if len(message.strip()) < 10:
                await self._buffer_message(sender, message)
                return
            
            # Process the message normally
            await self._process_message(sender, message)
            
        except Exception as e:
            logger.error(f"Error handling message from {sender}: {str(e)}")
            await self.handle_error(sender, str(e))
    
    async def _buffer_message(self, sender: str, message: str):
        """
        Buffer short messages to combine them before sending to the API.
        
        Args:
            sender (str): Sender's username
            message (str): Message content
        """
        # Initialize buffer for this user if it doesn't exist
        if sender not in self.message_buffers:
            self.message_buffers[sender] = {
                'messages': [],
                'last_update': asyncio.get_event_loop().time(),
                'task': None
            }
        
        buffer = self.message_buffers[sender]
        
        # Add message to buffer
        buffer['messages'].append(message)
        buffer['last_update'] = asyncio.get_event_loop().time()
        
        # Cancel existing task if there is one
        if buffer['task'] and not buffer['task'].done():
            buffer['task'].cancel()
        
        # Create a new task to process the buffer after a delay
        buffer['task'] = asyncio.create_task(self._process_buffer_after_delay(sender, 1.5))  # 1.5 second delay
        
        # Send typing notification to indicate we're listening
        await self.aim_handler.send_typing_notification(sender, True)
    
    async def _process_buffer_after_delay(self, sender: str, delay: float):
        """
        Process the message buffer after a delay.
        
        Args:
            sender (str): Sender's username
            delay (float): Delay in seconds
        """
        try:
            await asyncio.sleep(delay)
            
            if sender in self.message_buffers and self.message_buffers[sender]['messages']:
                # Combine messages in the buffer
                combined_message = " ".join(self.message_buffers[sender]['messages'])
                
                # Clear the buffer
                self.message_buffers[sender]['messages'] = []
                
                # Process the combined message
                await self._process_message(sender, combined_message)
        
        except asyncio.CancelledError:
            # Task was cancelled, likely because a new message arrived
            pass
    
    async def _process_message(self, sender: str, message: str):
        """
        Process a message and send it to the Dify API.
        
        Args:
            sender (str): Sender's username
            message (str): Message content
        """
        # Mark this user as being processed
        self.processing_users[sender] = True
        
        # Add a natural delay before showing typing indicator (1-3 seconds)
        delay = 1 + (uuid.uuid4().int % 2)  # Random delay between 1-3 seconds
        await asyncio.sleep(delay)
        
        # Send typing notification
        await self.aim_handler.send_typing_notification(sender, True)
        
        # Create a task for sending periodic typing notifications
        typing_task = asyncio.create_task(self._send_periodic_typing(sender))
        
        try:
            # Send the message to Dify API using the AIM username as the user identifier
            response_text, metadata = await self.dify_client.send_message(sender, message)
            
            # Cancel the typing notification task
            typing_task.cancel()
            
            # Send "stopped typing" notification
            await self.aim_handler.send_typing_notification(sender, False)
            
            # Send the response back to the AIM user
            await self.send_response(sender, response_text)
            
            # Process any buffered messages that came in while we were processing
            await self._process_buffered_messages(sender)
            
        except asyncio.CancelledError:
            logger.warning(f"Message processing for {sender} was cancelled")
            await self.aim_handler.send_typing_notification(sender, False)
        except Exception as e:
            logger.error(f"Error processing message from {sender}: {str(e)}")
            await self.handle_error(sender, str(e))
        finally:
            # Ensure typing task is cancelled
            if typing_task and not typing_task.done():
                typing_task.cancel()
            
            # Mark this user as no longer being processed
            self.processing_users[sender] = False
    
    async def _process_buffered_messages(self, sender: str):
        """
        Process any messages that were buffered while waiting for an API response.
        
        Args:
            sender (str): Sender's username
        """
        if sender in self.message_buffers and self.message_buffers[sender]['messages']:
            # Combine messages in the buffer
            combined_message = " ".join(self.message_buffers[sender]['messages'])
            logger.info(f"Processing buffered messages for {sender}: {combined_message}")
            
            # Clear the buffer
            self.message_buffers[sender]['messages'] = []
            
            # Process the combined message
            await self._process_message(sender, combined_message)
    
    async def _handle_clear_command(self, sender: str):
        """
        Handle the "clear" command from a user.
        
        Args:
            sender (str): Sender's username
        """
        logger.info(f"Clearing conversation history for {sender}")
        
        try:
            # Clear the conversation in Dify client
            # Note: We pass the sender directly since Dify uses it as the user ID
            await self.dify_client.clear_conversation(sender)
            
            # Clear all local state for this user
            if sender in self.user_sessions:
                del self.user_sessions[sender]
                logger.debug(f"Removed session mapping for user {sender}")
            
            # Cancel and clear any pending message buffer tasks
            if sender in self.message_buffers:
                if 'task' in self.message_buffers[sender] and not self.message_buffers[sender]['task'].done():
                    self.message_buffers[sender]['task'].cancel()
                self.message_buffers[sender] = {
                    'messages': [],
                    'last_update': asyncio.get_event_loop().time(),
                    'task': None
                }
                logger.debug(f"Reset message buffer for user {sender}")
            
            # Reset processing state
            self.processing_users[sender] = False
            
            # Send confirmation message
            confirmation = "Memory cleared. Your next message will be treated as the start of a new conversation."
            await self.aim_handler.send_message(sender, confirmation)
            logger.info(f"Sent clear confirmation to {sender}")
            
        except Exception as e:
            logger.error(f"Error clearing conversation for {sender}: {str(e)}")
            error_message = "Sorry, I encountered an error clearing the conversation. Please try again in a moment."
            await self.aim_handler.send_message(sender, error_message)
    
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
        # Check for specific error types and provide user-friendly messages
        if "429" in error or "Too many tokens" in error or "rate limit" in error.lower():
            error_message = "I'm receiving too many messages too quickly. Please wait a moment before sending more messages."
        elif "400" in error and "blank" in error:
            error_message = "I had trouble processing your short message. Please try sending a more complete message."
        else:
            # Generic error message for other errors
            error_message = "Sorry, I encountered an error processing your message. Please try again in a moment."
        
        # Log the detailed error for debugging
        logger.error(f"Error details for {recipient}: {error}")
        
        # Send the user-friendly error message
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
