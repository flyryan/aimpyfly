#!/usr/bin/env python3
"""
Test script to verify the fix for the "clear" command issue.
This script simulates the flow of messages that caused the error.
"""
import asyncio
import logging
import uuid
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_clear_command")

class MockDifyClient:
    """Mock Dify client for testing."""
    
    def __init__(self):
        self.conversations = {}
        logger.info("Initialized mock Dify client")
    
    async def send_message(self, session_id: str, message: str):
        """Mock sending a message to Dify API."""
        logger.info(f"Sending message with session ID: {session_id}, message: {message}")
        return f"Response to: {message}", {"metadata": "test"}
    
    async def clear_conversation(self, session_id: str):
        """Mock clearing a conversation."""
        # Simulate ending the conversation with Dify API
        logger.info(f"Simulating API call to end conversation with session ID: {session_id}")
        
        # Remove any conversations associated with this session ID
        to_remove = []
        for user_id, conv_id in self.conversations.items():
            if conv_id == session_id:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self.conversations[user_id]
            logger.info(f"Cleared conversation for session: {session_id}")
        
        return True

class MockAIMHandler:
    """Mock AIM handler for testing."""
    
    def __init__(self):
        logger.info("Initialized mock AIM handler")
    
    async def send_message(self, recipient: str, message: str):
        """Mock sending a message to AIM."""
        logger.info(f"Sending message to {recipient}: {message}")
        return True
    
    async def send_typing_notification(self, recipient: str, typing_status: bool):
        """Mock sending typing notification."""
        status = "typing" if typing_status else "stopped typing"
        logger.info(f"Sending {status} notification to {recipient}")
        return True

class TestBot:
    """Test bot class to simulate the AIMBot behavior."""
    
    def __init__(self):
        self.dify_client = MockDifyClient()
        self.aim_handler = MockAIMHandler()
        self.user_sessions = {}
        self.message_buffers = {}
        self.processing_users = {}
        logger.info("Initialized test bot")
    
    async def test_clear_command_scenario(self):
        """Test the scenario that caused the error."""
        sender = "test_user"
        
        # Step 1: User sends a message
        logger.info("\n--- Step 1: User sends initial message ---")
        await self.handle_message(sender, "Hello, how are you?")
        initial_session = self.user_sessions.get(sender)
        logger.info(f"Initial session ID: {initial_session}")
        
        # Step 2: User sends clear command
        logger.info("\n--- Step 2: User sends clear command ---")
        await self.handle_message(sender, "clear")
        
        # Verify session was cleared
        logger.info(f"Session after clear: {self.user_sessions.get(sender, 'None')}")
        
        # Step 3: User sends another message after clearing
        logger.info("\n--- Step 3: User sends message after clearing ---")
        await self.handle_message(sender, "test")
        new_session = self.user_sessions.get(sender)
        logger.info(f"New session ID: {new_session}")
        
        # Verify that a new session was created and it's different from the initial one
        if initial_session != new_session:
            logger.info("✓ Test passed: New session ID is different from initial session ID")
        else:
            logger.error("✗ Test failed: New session ID is the same as initial session ID")
        
        # Verify all state is clean
        logger.info("\nFinal state:")
        logger.info(f"- User sessions: {self.user_sessions}")
        logger.info(f"- Message buffers: {self.message_buffers}")
        logger.info(f"- Processing users: {self.processing_users}")
    
    async def handle_message(self, sender: str, message: str):
        """Simulate the handle_message method from AIMBot."""
        logger.info(f"Processing message from {sender}: {message}")
        
        # Check if this is a "clear" command
        if message.strip().lower() == "clear":
            await self._handle_clear_command(sender)
            return
        
        # Get or create a session ID for this user
        session_id = self.user_sessions.get(sender)
        if not session_id:
            session_id = str(uuid.uuid4())
            self.user_sessions[sender] = session_id
            logger.info(f"Created new session for {sender}: {session_id}")
        
        # Process the message
        await self._process_message(sender, message)
    
    async def _handle_clear_command(self, sender: str):
        """Simulate the _handle_clear_command method from AIMBot."""
        logger.info(f"Clearing conversation history for {sender}")
        
        try:
            # Clear the conversation in Dify client
            session_id = self.user_sessions.get(sender)
            if session_id:
                # Clear the conversation using the session ID
                await self.dify_client.clear_conversation(session_id)
                # Remove the session ID from our mapping
                del self.user_sessions[sender]
                logger.debug(f"Removed session ID {session_id} for user {sender}")
            
            # Also clear any message buffers for this user
            if sender in self.message_buffers:
                self.message_buffers[sender] = {}
                logger.debug(f"Cleared message buffer for user {sender}")
            
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
    
    async def _process_message(self, sender: str, message: str):
        """Simulate the _process_message method from AIMBot."""
        try:
            # Get or create a session ID for this user
            session_id = self.user_sessions.get(sender)
            if not session_id:
                session_id = str(uuid.uuid4())
                self.user_sessions[sender] = session_id
                logger.info(f"Created new session for {sender}: {session_id}")
            
            # Send the message to Dify API
            response_text, metadata = await self.dify_client.send_message(session_id, message)
            
            # Send the response back to the AIM user
            await self.aim_handler.send_message(sender, response_text)
            
        except Exception as e:
            logger.error(f"Error processing message from {sender}: {str(e)}")

async def main():
    """Main test function."""
    logger.info("Starting clear command test")
    test_bot = TestBot()
    await test_bot.test_clear_command_scenario()
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main())
