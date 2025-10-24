"""Logging configuration for the requirements management system."""
import logging
import sys
from pathlib import Path
from typing import Optional
from backend.config.config import settings

class SafeColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output and Unicode safety."""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Safely encode the message to handle Unicode characters
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # If encoding fails, replace problematic characters
            record.msg = self._safe_encode(record.msg)
            return super().format(record)
    
    def _safe_encode(self, text):
        """Safely encode text by replacing problematic Unicode characters."""
        if isinstance(text, str):
            # Replace problematic Unicode characters with similar ASCII equivalents
            replacements = {
                '\u202f': ' ',  # Narrow no-break space -> regular space
                '\u00a0': ' ',  # No-break space -> regular space
                '\u2018': "'",  # Left single quotation mark
                '\u2019': "'",  # Right single quotation mark
                '\u201c': '"',  # Left double quotation mark
                '\u201d': '"',  # Right double quotation mark
                '\u2013': '-',  # En dash
                '\u2014': '-',  # Em dash
            }
            for unicode_char, replacement in replacements.items():
                text = text.replace(unicode_char, replacement)
        return text

def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """Set up a logger with console and optional file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers.clear()
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = SafeColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with UTF-8 encoding
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

logger = setup_logger("requirements_management", log_level=settings.log_level, log_file=settings.log_file)