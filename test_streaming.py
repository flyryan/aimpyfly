#!/usr/bin/env python3
"""
Script to test the streaming mode of the Dify API.
This allows for testing the streaming response handling without the AIM integration.
"""
import asyncio
import os
import json
import aiohttp
import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("test_streaming")

# Dify API configuration
API_KEY = "app-ONu0R9S3wESNtJyZRRjZKscX"  # Replace with your Dify API key
API_URL = "http://52.89.105.190/v1"

async def test_streaming_mode():
    """Test the streaming mode of the Dify API."""
    url = f"{API_URL}/chat-messages"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use a simple query for testing
    payload = {
        "query": "Hello, who are you?",
        "user": f"test_user_{int(time.time())}",  # Use unique user ID
        "response_mode": "streaming",
        "conversation_id": "",
        "inputs": {}
    }
    
    logger.info(f"Starting streaming request test with payload: {payload}")
    
    # Buffer for collecting chunks
    buffer = []
    raw_lines = []  # Store raw lines for debugging
    metadata = {}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"API error: {response.status} - {error_text}")
                return
            
            logger.info(f"Streaming response started. Status: {response.status}, Headers: {response.headers}")
            
            # Process the stream
            async for line in response.content:
                if not line:
                    continue
                
                line_str = line.decode('utf-8').strip()
                raw_lines.append(line_str)  # Store raw line for debugging
                
                logger.debug(f"Raw line: {line_str}")
                
                if not line_str or line_str == 'data: [DONE]':
                    continue
                
                # Remove 'data: ' prefix if present
                if line_str.startswith('data: '):
                    line_str = line_str[6:]
                
                try:
                    event_data = json.loads(line_str)
                    event_type = event_data.get('event')
                    data = event_data.get('data', {})
                    
                    logger.info(f"Event type: {event_type}, Data: {data}")
                    
                    if event_type == 'message':
                        # Standard format (text field)
                        text_chunk = data.get('text', '')
                        buffer.append(text_chunk)
                        logger.info(f"Chunk #{len(buffer)} received: '{text_chunk}'")
                    
                    elif event_type == 'agent_message':
                        # Agent format (answer field directly in event_data)
                        answer_chunk = event_data.get('answer', '')
                        if answer_chunk:
                            buffer.append(answer_chunk)
                            logger.info(f"Agent message chunk received: '{answer_chunk}'")
                    
                    elif event_type == 'message_end':
                        # This is the end of the stream with metadata
                        metadata = {
                            "conversation_id": event_data.get("conversation_id", ""),
                            "created_at": event_data.get("created_at", 0),
                            "id": event_data.get("id", "")
                        }
                        logger.info(f"Stream ended. Metadata: {metadata}")
                
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing response: {e} - Line: {line_str}")
                    # Try to extract text directly using string operations
                    if 'text' in line_str:
                        try:
                            start_idx = line_str.find('"text":"') + 8
                            if start_idx > 8:  # Found "text":"
                                end_idx = line_str.find('"', start_idx)
                                if end_idx > start_idx:
                                    text = line_str[start_idx:end_idx]
                                    logger.info(f"Extracted text directly: '{text}'")
                                    buffer.append(text)
                        except Exception as ex:
                            logger.error(f"Error extracting text directly: {ex}")
    
    # Combine all chunks into the final response
    complete_response = ''.join(buffer)
    logger.info(f"Complete response length: {len(complete_response)}")
    
    if complete_response:
        logger.info(f"Complete response: '{complete_response}'")
    else:
        logger.warning("No response content received!")
        
        # Try to extract content directly from raw lines
        for line in raw_lines:
            if 'text' in line:
                logger.info(f"Line with 'text': {line}")
    
    # Write the complete response to a file for inspection
    with open("streaming_response.txt", "w") as f:
        f.write(complete_response)
    
    # Write raw response to file for debugging
    with open("streaming_raw_response.txt", "w") as f:
        f.write("\n".join(raw_lines))
    
    logger.info("Complete response written to streaming_response.txt")
    logger.info("Raw response written to streaming_raw_response.txt")

if __name__ == "__main__":
    asyncio.run(test_streaming_mode())