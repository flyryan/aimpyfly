"""
Configuration management for the AIM chatbot.
Loads environment variables from .env file and provides access to them.
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AIM Configuration
AIM_USERNAME = os.getenv("AIM_USERNAME", "AIGURU9000")
AIM_PASSWORD = os.getenv("AIM_PASSWORD", "password1")
AIM_SERVER = os.getenv("AIM_SERVER", "aim.visionfun.org")
AIM_PORT = int(os.getenv("AIM_PORT", "5190"))

# Dify API Configuration
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "app-5kmGGYfP4z0omMEfNYVaLW8B")
DIFY_API_URL = os.getenv("DIFY_API_URL", "http://52.89.105.190/v1")

# Logging Configuration
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

LOG_LEVEL = LOG_LEVEL_MAP.get(os.getenv("LOG_LEVEL", "DEBUG"), logging.DEBUG)
LOG_FILE = os.getenv("LOG_FILE", "aimbot.log")

# API Mode (blocking due to AIM limitations)
API_MODE = "blocking"

def get_aim_credentials():
    """Return AIM credentials as a dictionary."""
    return {
        "username": AIM_USERNAME,
        "password": AIM_PASSWORD,
        "server": AIM_SERVER,
        "port": AIM_PORT
    }

def get_dify_config():
    """Return Dify API configuration as a dictionary."""
    return {
        "api_key": DIFY_API_KEY,
        "api_url": DIFY_API_URL,
        "mode": API_MODE
    }

def get_logging_config():
    """Return logging configuration as a dictionary."""
    return {
        "level": LOG_LEVEL,
        "file": LOG_FILE
    }
