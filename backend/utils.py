import logging
import re
from typing import Any, Dict

def setup_logger(name: str, log_file: str = 'logs/backend.log', level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Ensure directory exists
    import os
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

def sanitize_text(text: str) -> str:
    """Removes special characters and extra whitespace."""
    if not text:
        return ""
    text = re.sub(r'[^\w\s.,?!-]', '', text)
    return " ".join(text.split())

def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely retrieve a value from a dictionary."""
    return data.get(key, default)
