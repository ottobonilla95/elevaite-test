import re
from typing import Optional


def process_log(log: str, filter_fastapi: bool = False) -> Optional[str]:
    """
    Processes a log string by:
      1. Removing the bracketed prefix.
      2. Optionally filtering out regular FastAPI logs (if filter_fastapi is True).

    Args:
        log (str): The log string to process.
        filter_fastapi (bool, optional): If True, logs starting with standard HTTP methods
                                         (e.g. POST, GET, PUT, etc.) are ignored (None is returned).
                                         Defaults to False.

    Returns:
        Optional[str]: The cleaned log string, or None if it was filtered out.
    """
    # Remove leading square-bracketed prefix
    cleaned = re.sub(r"^\[[^\]]*\]\s*", "", log)

    if filter_fastapi:
        # Check for standard HTTP methods at the start of the cleaned log message
        if re.match(r"^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s", cleaned):
            # If it's a typical FastAPI log message, return None to indicate it's ignored
            return None

    return cleaned
