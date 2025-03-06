"""
Logging configuration for the AIM chatbot.
Provides a custom logger with colorized output.
"""
import logging
import os
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

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
