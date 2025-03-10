"""
Dify API client for the AIM chatbot.
Handles communication with the Dify Chat API.
"""
import json
import aiohttp
import uuid
from typing import Dict, Any, Optional, List, Tuple

from aimbot.utils.logger import get_logger

logger = get_logger(__name__)

class DifyClient:
    """
    Client for interacting with the Dify Chat API.
    
    Attributes:
        api_key (str): Dify API key
        api_url (str): Dify API base URL
        mode (str): Response mode (streaming or blocking)
        session (aiohttp.ClientSession): HTTP session for API requests
    """
    
    def __init__(self, api_key: str, api_url: str, mode: str = "blocking"):
        """
        Initialize the Dify API client.
        
        Args:
            api_key (str): Dify API key
            api_url (str): Dify API base URL
            mode (str, optional): Response mode (streaming or blocking). Defaults to "blocking".
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.mode = mode
        self.session = None
        self.conversations: Dict[str, str] = {}  # Map user_id to conversation_id
        
        logger.debug(f"Initialized Dify client with API URL: {api_url}, Mode: {mode}")
    
    async def _ensure_session(self):
        """Ensure that the HTTP session is created."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            logger.debug("Created new aiohttp session")
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Closed aiohttp session")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the HTTP headers for API requests.
        
        Returns:
            Dict[str, str]: HTTP headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_conversation(self, user_id: str) -> str:
        """
        Create a new conversation.
        
        Args:
            user_id (str): User identifier
            
        Returns:
            str: Conversation ID
        """
        # In Dify, conversations are created automatically when sending the first message
        # We'll generate a UUID to use as a placeholder until we get a real conversation ID
        conversation_id = str(uuid.uuid4())
        self.conversations[user_id] = conversation_id
        logger.debug(f"Created placeholder conversation ID for user {user_id}: {conversation_id}")
        return conversation_id
    
    async def clear_conversation(self, user_id: str) -> bool:
        """
        Clear a user's conversation history.
        
        Args:
            user_id (str): User identifier
            
        Returns:
            bool: True if conversation was cleared, False otherwise
        """
        try:
            # Simply remove the conversation ID from our mapping
            # Next message will start a new conversation automatically
            if user_id in self.conversations:
                del self.conversations[user_id]
                logger.info(f"Cleared conversation history for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation for user {user_id}: {str(e)}")
            return False
    
    async def send_message(self, user_id: str, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Send a message to the Dify Chat API.
        
        Args:
            user_id (str): User identifier
            message (str): Message content
            
        Returns:
            Tuple[str, Dict[str, Any]]: Response text and metadata
        """
        await self._ensure_session()
        
        # Get conversation ID for this user if it exists
        conversation_id = self.conversations.get(user_id, "")
        
        # Prepare request payload
        payload = {
            "query": message,
            "user": user_id,
            "response_mode": self.mode,
            "conversation_id": conversation_id,  # Empty string for new conversation
            "inputs": {}  # Required by Dify API even if empty
        }
        
        logger.debug(f"Sending message to Dify API: {payload}")
        
        try:
            # Handle differently based on response mode
            if self.mode == "blocking":
                return await self._handle_blocking_request(user_id, payload)
            elif self.mode == "streaming":
                return await self._handle_streaming_request(user_id, payload)
            else:
                logger.error(f"Unsupported response mode: {self.mode}")
                return f"Error: Unsupported response mode {self.mode}", {}
                
        except aiohttp.ClientError as e:
            logger.error(f"Dify API request error: {str(e)}")
            return f"Error: {str(e)}", {}
    
    async def _handle_blocking_request(self, user_id: str, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Handle a blocking request to the Dify API.
        
        Args:
            user_id (str): User identifier
            payload (Dict[str, Any]): Request payload
            
        Returns:
            Tuple[str, Dict[str, Any]]: Response text and metadata
        """
        async with self.session.post(
            f"{self.api_url}/chat-messages",
            headers=self._get_headers(),
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Dify API error: {response.status} - {error_text}")
                return f"Error: {response.status}", {}
            
            data = await response.json()
            
            # Store the conversation ID for future messages
            if "conversation_id" in data:
                self.conversations[user_id] = data["conversation_id"]
                logger.debug(f"Updated conversation ID for user {user_id}: {data['conversation_id']}")
            
            # Extract the answer and metadata
            answer = data.get("answer", "")
            metadata = {
                "conversation_id": data.get("conversation_id", ""),
                "created_at": data.get("created_at", 0),
                "id": data.get("id", "")
            }
            
            logger.debug(f"Received blocking response from Dify API: {len(answer)} chars")
            
            return answer, metadata
    
    async def _handle_streaming_request(self, user_id: str, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Handle a streaming request to the Dify API.
        
        Args:
            user_id (str): User identifier
            payload (Dict[str, Any]): Request payload
            
        Returns:
            Tuple[str, Dict[str, Any]]: Complete response text and metadata
        """
        # For streaming, we need to buffer the response chunks
        buffer = []
        metadata = {}
        raw_lines = []  # Store raw lines for debugging
        
        logger.debug(f"Starting streaming request for user {user_id}")
        
        async with self.session.post(
            f"{self.api_url}/chat-messages",
            headers=self._get_headers(),
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Dify API error: {response.status} - {error_text}")
                return f"Error: {response.status}", {}
            
            logger.debug(f"Response headers: {response.headers}")
            
            # Process the stream
            async for line in response.content:
                if not line:
                    continue
                
                line_str = line.decode('utf-8').strip()
                raw_lines.append(line_str)  # Store raw line for debugging
                
                if not line_str or line_str == 'data: [DONE]':
                    continue
                
                # Log raw line for debugging (first few and last few)
                if len(raw_lines) <= 3 or len(raw_lines) % 50 == 0:
                    logger.debug(f"Raw line: {line_str}")
                
                # Remove 'data: ' prefix if present
                if line_str.startswith('data: '):
                    line_str = line_str[6:]
                
                try:
                    event_data = json.loads(line_str)
                    event_type = event_data.get('event')
                    
                    # Handle different event types
                    if event_type == 'message':
                        # Standard format (text field)
                        data = event_data.get('data', {})
                        text_chunk = data.get('text', '')
                        buffer.append(text_chunk)
                        logger.debug(f"Received 'message' chunk #{len(buffer)} for {user_id}: '{text_chunk}'")
                    
                    elif event_type == 'agent_message':
                        # Agent format (answer field directly in event_data)
                        answer_chunk = event_data.get('answer', '')
                        if answer_chunk:
                            buffer.append(answer_chunk)
                            # Only log occasionally to avoid flooding the console
                            if len(buffer) <= 3 or len(buffer) % 10 == 0:
                                logger.debug(f"Received 'agent_message' chunk #{len(buffer)} for {user_id}: '{answer_chunk}'")
                    
                    elif event_type == 'message_end':
                        # Standard format end event or agent format end event
                        conversation_id = event_data.get('conversation_id', '')
                        if conversation_id:
                            self.conversations[user_id] = conversation_id
                            logger.debug(f"Updated conversation ID for user {user_id}: {conversation_id}")
                        
                        metadata = {
                            "conversation_id": conversation_id,
                            "created_at": event_data.get("created_at", 0),
                            "id": event_data.get("id", "")
                        }
                        logger.debug(f"Received message_end event: {metadata}")
                    
                    elif event_type == 'agent_thought':
                        # Agent thought event - store conversation ID if present
                        conversation_id = event_data.get('conversation_id', '')
                        if conversation_id:
                            self.conversations[user_id] = conversation_id
                            logger.debug(f"Updated conversation ID from agent_thought for {user_id}: {conversation_id}")
                        
                        # Extract thought content if available
                        thought = event_data.get('thought', '')
                        if thought and not buffer:  # Only use thought if buffer is empty
                            buffer.append(thought)
                            logger.debug(f"Using thought as fallback content: '{thought[:50]}...'")
                        
                        # Note: Removed duplicate code and reference to undefined 'data' variable
                
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing streaming response: {e} - Line: {line_str}")
                    continue
        
        # Combine all chunks into the final response
        complete_response = ''.join(buffer)
        
        # If buffer is empty but we have raw lines, try to extract content directly
        if not complete_response and raw_lines:
            logger.warning(f"Buffer is empty but received {len(raw_lines)} raw lines. Attempting direct extraction.")
            
            # First try to extract from agent_message events
            for line in raw_lines:
                if '"event":"agent_message"' in line and '"answer":"' in line:
                    try:
                        # Extract answer directly using string operations
                        start_idx = line.find('"answer":"') + 9
                        if start_idx > 9:  # Found "answer":"
                            end_idx = line.find('"', start_idx)
                            if end_idx > start_idx:
                                text = line[start_idx:end_idx]
                                buffer.append(text)
                                logger.debug(f"Extracted answer directly: '{text}'")
                    except Exception as e:
                        logger.error(f"Error extracting answer directly: {e}")
            
            # If still empty, try to extract from agent_thought events
            if not buffer:
                for line in raw_lines:
                    if '"event":"agent_thought"' in line and '"thought":"' in line:
                        try:
                            start_idx = line.find('"thought":"') + 10
                            if start_idx > 10:  # Found "thought":"
                                end_idx = line.find('"', start_idx)
                                if end_idx > start_idx:
                                    text = line[start_idx:end_idx]
                                    buffer.append(text)
                                    logger.debug(f"Extracted thought directly: '{text}'")
                                    break  # Just use the first complete thought
                        except Exception as e:
                            logger.error(f"Error extracting thought directly: {e}")
            
            # Try again with the extracted content
            complete_response = ''.join(buffer)
            
            # If still empty, use a default response
            if not complete_response:
                logger.error("Failed to extract any content from streaming response")
                complete_response = "I'm sorry, I encountered an issue processing your request."
        
        logger.info(f"Completed streaming response for {user_id}, length: {len(complete_response)}")
        if complete_response:
            logger.debug(f"Response preview: '{complete_response[:100]}...'")
        
        # Write raw response to file for debugging
        try:
            with open(f"streaming_debug_{user_id}.txt", "w") as f:
                f.write("\n".join(raw_lines))
            logger.debug(f"Wrote raw streaming response to streaming_debug_{user_id}.txt")
        except Exception as e:
            logger.error(f"Error writing debug file: {e}")
        
        return complete_response, metadata
    
    async def handle_response(self, response: Dict[str, Any]) -> str:
        """
        Process the API response.
        
        Args:
            response (Dict[str, Any]): API response
            
        Returns:
            str: Processed response text
        """
        # Extract the answer from the response
        if isinstance(response, dict):
            return response.get("answer", "")
        
        # If it's already a string (from streaming mode), return it directly
        if isinstance(response, str):
            return response
        
        # Fallback
        logger.warning(f"Unexpected response type: {type(response)}")
        return str(response)
