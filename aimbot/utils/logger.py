"""
Logging configuration for the AIM chatbot.
Provides a custom logger with colorized output and conversation logging capabilities.
"""
import logging
import os
from datetime import datetime
from colorama import Fore, Style, init
from aimbot.config.settings import CONVERSATION_LOG_DIR

# Initialize colorama
init(autoreset=True)

class ConversationLogger:
    """
    Handles logging of conversations for individual bots and their users.
    Creates separate log files for each user's conversations with timestamps.
    """
    def __init__(self, bot_name):
        """
        Initialize conversation logger.
        
        Args:
            bot_name (str): Name of the bot (unused, kept for compatibility)
        """
        self.base_dir = CONVERSATION_LOG_DIR
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Create the bot's conversation directory if it doesn't exist."""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
    
    def _get_log_file(self, user_id):
        """
        Get the log file path for a specific user.
        
        Args:
            user_id (str): User identifier for file naming
            
        Returns:
            str: Path to the user's log file
        """
        return os.path.join(self.base_dir, f"{user_id}.log")
    
    def log_message(self, user_id, message, is_from_user=True):
        """
        Log a conversation message with timestamp.
        
        Args:
            user_id (str): User identifier
            message (str): Message content
            is_from_user (bool): True if message is from user, False if from bot
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        direction = user_id if is_from_user else "Bot"
        log_entry = f"[{timestamp}] {direction}: {message}\n"
        
        with open(self._get_log_file(user_id), 'a', encoding='utf-8') as f:
            f.write(log_entry)

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter for colorized log output.
    """
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
            record.msg = f"{self.COLORS[levelname]}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

def setup_logger(name, level=logging.DEBUG, log_file=None):
    """
    Set up and return a logger with the specified name, level, and optional file output.
    
    Args:
        name (str): Logger name
        level (int): Logging level (default: DEBUG)
        log_file (str, optional): Path to log file
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler with custom formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        # Create directory for log file if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name, config=None):
    """
    Get a logger with the specified name and configuration.
    
    Args:
        name (str): Logger name
        config (dict, optional): Configuration dictionary with 'level' and 'file' keys
        
    Returns:
        logging.Logger: Configured logger
    """
    if config is None:
        # Import here to avoid circular imports
        from aimbot.config.settings import get_logging_config
        config = get_logging_config()
    
    return setup_logger(name, config['level'], config.get('file'))
