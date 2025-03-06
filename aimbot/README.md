# AIM Chatbot

An AI-powered chatbot for AOL Instant Messenger (AIM) that integrates with the Dify Chat API.

## Overview

This project connects to AOL Instant Messenger through the Aimpyfly library and uses the Dify Chat API to provide intelligent responses to messages. It bridges classic instant messaging with modern AI capabilities.

## Features

- Connect to AIM servers using the Aimpyfly library
- Process messages through Dify's AI
- Support for conversation persistence
- Automatic reconnection on disconnection
- Configurable logging
- Environment-based configuration

## Requirements

- Python 3.7+
- Aimpyfly library
- Dify API key
- AIM credentials

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and update with your credentials:
   ```
   cp .env.example .env
   ```

## Configuration

Edit the `.env` file with your credentials:

```
# AIM Configuration
AIM_USERNAME=your_aim_username
AIM_PASSWORD=your_aim_password
AIM_SERVER=aim.visionfun.org
AIM_PORT=5190

# Dify API
DIFY_API_KEY=your_dify_api_key
DIFY_API_URL=http://52.89.105.190/v1

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=aimbot.log
```

## Usage

Run the bot:

```
python -m aimbot.main
```

The bot will connect to the AIM server and start processing messages. Any messages sent to the bot's AIM account will be processed through the Dify API, and the response will be sent back to the sender.

## Project Structure

```
aimbot/
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration management
├── api/
│   ├── __init__.py
│   └── dify_client.py    # Dify API integration
├── bot/
│   ├── __init__.py
│   ├── aim_handler.py    # AIM message handling
│   └── bot.py           # Main bot class
├── utils/
│   ├── __init__.py
│   └── logger.py        # Logging configuration
├── .env.example         # Environment variables template
├── main.py             # Entry point
└── README.md           # Documentation
```

## Error Handling

The bot includes robust error handling:

- Automatic reconnection to AIM on disconnection
- Rate limiting for message sending
- Error logging
- Graceful degradation on API failures

## Logging

Logs are written to both the console and a log file (if configured). The log level can be configured in the `.env` file.

## License

This project is licensed under the MIT License.
