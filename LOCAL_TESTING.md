# Local Testing Guide

This guide explains how to run and test the AIM bot locally, outside of Docker containers.

## Prerequisites

- Python 3.7+
- Required Python packages (install with `pip install -r requirements.txt`)
- AIM credentials

## Running the Bot Locally

### Using the run_local.py Script

The `run_local.py` script is configured to run the bot locally with streaming mode enabled:

```bash
# Make the script executable
chmod +x run_local.py

# Run the bot
./run_local.py
```

You can edit the script to modify environment variables like API keys, credentials, etc.

### Using the run_bot.sh Script

The `run_bot.sh` script provides command-line options to run the bot with different modes:

```bash
# Make the script executable
chmod +x run_bot.sh

# Run with streaming mode
./run_bot.sh --streaming

# Run with blocking mode
./run_bot.sh --blocking

# Run with debug logging
./run_bot.sh --streaming --debug
```

Use `./run_bot.sh --help` for more options.

## Testing Streaming Mode

To test the streaming mode without the AIM integration, use the `test_streaming.py` script:

```bash
# Make the script executable
chmod +x test_streaming.py

# Run the test
./test_streaming.py
```

This script will:
1. Send a request to the Dify API in streaming mode
2. Log each chunk as it's received
3. Combine all chunks into a complete response
4. Save the complete response to `streaming_response.txt` for inspection

## Debugging Tips

1. **Check Logs**: Set the log level to DEBUG for more detailed logs:
   ```bash
   ./run_bot.sh --streaming --debug
   ```

2. **Monitor Network Traffic**: Use tools like Wireshark to monitor network traffic between the bot and the AIM server.

3. **Test API Directly**: Use the `test_streaming.py` script to test the Dify API directly without the AIM integration.

4. **Inspect Response**: Check the `streaming_response.txt` file to see the complete response from the Dify API.

## Common Issues

1. **Connection Drops**: If the AIM connection drops during streaming:
   - Try reducing the response size by asking shorter questions
   - Check network stability
   - Ensure the AIM server is not rate-limiting the bot

2. **Slow Responses**: If responses seem slow:
   - The streaming buffer might be working correctly, but large responses take time to generate
   - The bot will show a typing indicator while buffering the response

3. **Truncated Messages**: If messages are cut off:
   - This is by design - AIM has message size limits
   - Very long responses will be truncated to fit within AIM's limits