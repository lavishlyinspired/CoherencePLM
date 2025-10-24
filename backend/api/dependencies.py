"""Dependencies and shared utilities for API routes."""
from datetime import datetime
from backend.logger.logger import logger

def safe_log_message(message: str) -> str:
    """Safely encode message for logging by replacing problematic Unicode characters."""
    replacements = {
        '\u202f': ' ',  # Narrow no-break space -> regular space
        '\u00a0': ' ',  # No-break space -> regular space
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash,
    }
    for unicode_char, replacement in replacements.items():
        message = message.replace(unicode_char, replacement)
    return message