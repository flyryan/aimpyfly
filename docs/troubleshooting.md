# Troubleshooting Guide

This document provides solutions for common issues that may arise when running the AIM chatbot.

## Table of Contents

1. [Connection Issues](#connection-issues)
2. [Message Processing Issues](#message-processing-issues)
3. [API Integration Issues](#api-integration-issues)
4. [Docker Container Issues](#docker-container-issues)

## Connection Issues

### Unable to Connect to AIM Server

**Symptoms:**
- Bot fails to start with connection errors
- Logs show "Failed to connect to AIM server"

**Solutions:**
1. Verify AIM server is running and accessible
2. Check AIM credentials (username, password)
3. Ensure network connectivity to the AIM server
4. Verify the correct port is being used (default: 5190)

### Connection Drops Frequently

**Symptoms:**
- Bot disconnects unexpectedly
- Logs show reconnection attempts

**Solutions:**
1. Check network stability
2. Increase reconnection attempts in `aim_handler.py`
3. Implement more robust keep-alive mechanism

## Message Processing Issues

### "Clear" Command Errors

**Symptoms:**
- After using the "clear" command, subsequent messages result in errors
- Logs show error: `'messages'` when processing messages after clearing

**Solutions:**
1. Ensure session IDs are properly recreated after clearing:
   - In `bot.py`, both `handle_message` and `_process_message` methods should check if a session ID exists and create a new one if needed
   - Example fix:
   ```python
   # Get or create a session ID for this user
   session_id = self.user_sessions.get(sender)
   if not session_id:
       session_id = str(uuid.uuid4())
       self.user_sessions[sender] = session_id
       logger.debug(f"Created new session for {sender}: {session_id}")
   ```

2. In `dify_client.py`, ensure the `send_message` method handles empty conversation IDs properly:
   ```python
   # Get conversation ID for this user, or create a new one
   conversation_id = self.conversations.get(user_id, "")
   ```

### Short Messages Not Processing

**Symptoms:**
- Very short messages (less than 10 characters) don't receive responses
- Messages get stuck in buffer

**Solutions:**
1. Check the buffer processing logic in `_process_buffer_after_delay`
2. Ensure buffer tasks are being properly scheduled and executed
3. Verify typing notifications are being sent while buffering

## API Integration Issues

### Dify API Connection Failures

**Symptoms:**
- Error messages when sending messages to users
- Logs show API request errors

**Solutions:**
1. Verify API key is correct
2. Check API URL is accessible
3. Ensure proper error handling in `dify_client.py`

### Rate Limiting Issues

**Symptoms:**
- Error messages containing "429" or "rate limit"
- Intermittent failures when sending messages

**Solutions:**
1. Implement rate limiting in the bot
2. Add exponential backoff for retries
3. Consider using multiple API keys for high-volume instances

## Docker Container Issues

### Environment Variable Problems

**Symptoms:**
- Bot starts with default values instead of container-specific values
- Multiple containers use the same credentials

**Solutions:**
1. Ensure environment variables are properly set in `docker-compose.yml`
2. Verify `settings.py` is loading environment variables correctly
3. Use hardcoded values in docker-compose.yml instead of variable substitution

### Container Communication Issues

**Symptoms:**
- Containers can't communicate with each other
- Network-related errors in logs

**Solutions:**
1. Verify network configuration in docker-compose.yml
2. Check container names and hostnames
3. Ensure ports are properly exposed if needed

### Multiple Instance Issues

**Symptoms:**
- Conflicts between bot instances
- Shared resource problems

**Solutions:**
1. Ensure each container has unique:
   - AIM username and password
   - Dify API key
   - Log file name
2. Verify volume mounts are properly configured
3. Check for any shared state between containers
