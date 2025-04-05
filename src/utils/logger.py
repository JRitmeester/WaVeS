import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logging() -> logging.Logger:
    """
    Set up logging configuration for the application.
    Returns the root logger instance.
    """
    # Create logs directory in AppData
    log_dir = Path.home() / "AppData/Roaming/WaVeS/logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger("WaVeS")
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '[%(asctime)s] - %(levelname)s \t %(message)s'
    )
    console_formatter = logging.Formatter(
        '[%(asctime)s] - %(levelname)s \t %(message)s'
    )
    
    # Create and configure file handler with rotation
    log_file = log_dir / "waves.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=1024*1024,  # 1MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create a default logger instance
logger = setup_logging() 