import re
from datetime import timedelta

def is_valid_url(url: str) -> bool:
    if not url:
        return False
    pattern = re.compile(r"^(https?://|@|t\.me/|https://t.me/).+")
    return bool(pattern.match(url.strip()))

def format_remaining(seconds: int) -> tuple[int,int]:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return hours, minutes

def sanitize(text: str, max_len: int = 1000) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len]
    return text

def parse_int(text: str, min_val: int = 1, max_val: int = 100000) -> int | None:
    try:
        v = int(text.strip())
        if min_val <= v <= max_val:
            return v
    except:
        pass
    return None
