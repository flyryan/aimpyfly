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
        
        # Get conversation ID for this user, or create a new one
        conversation_id = self.conversations.get(user_id)
        
        # Prepare request payload
        payload = {
            "query": message,
            "user": user_id,
            "response_mode": self.mode,
            "conversation_id": conversation_id or "",
            "inputs": {}  # Required by Dify API even if empty
        }
        
        logger.debug(f"Sending message to Dify API: {payload}")
        
        try:
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
                metadata = data.get("metadata", {})
                
                logger.debug(f"Received response from Dify API: {len(answer)} chars")
                
                return answer, metadata
                
        except aiohttp.ClientError as e:
            logger.error(f"Dify API request error: {str(e)}")
            return f"Error: {str(e)}", {}
    
    async def handle_response(self, response: Dict[str, Any]) -> str:
        """
        Process the API response.
        
        Args:
            response (Dict[str, Any]): API response
            
        Returns:
            str: Processed response text
        """
        # In blocking mode, we just return the answer
        if self.mode == "blocking":
            return response.get("answer", "")
        
        # In streaming mode, we would process the stream chunks
        # But since we're using blocking mode for AIM, this is not implemented
        logger.warning("Streaming mode not implemented, using blocking mode")
        return response.get("answer", "")
