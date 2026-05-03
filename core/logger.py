import sys
from loguru import logger

def setup_logger(debug: bool = True):
    """Configures FRIDAY's logging system."""
    
    # Remove default logger
    logger.remove()
    
    # Console output — colourful and readable
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="DEBUG" if debug else "INFO"
    )
    
    # File output — full logs saved to friday.log
    logger.add(
        "friday.log",
        rotation="1 MB",      # starts a new log file after 1MB
        retention="7 days",   # deletes logs older than 7 days
        level="DEBUG",
        format="{time} | {level} | {message}"
    )
    
    logger.info("Logger initialized")