from __future__ import annotations

import hmac
import re
import time
import unicodedata
from collections import deque
from typing import Any

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def clean_text(value: Any, max_len: int = 500, allow_newlines: bool = True) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = CONTROL_CHARS.sub("", text)
    if not allow_newlines:
        text = " ".join(text.splitlines())
    text = text.strip()
    if len(text) > max_len:
        raise ValueError(f"Input is too long (maximum {max_len} characters).")
    return text


def normalize_email(value: str) -> str:
    return clean_text(value, 254, allow_newlines=False).lower()


def mask_email(email: str) -> str:
    email = normalize_email(email)
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    shown = local[:2] if len(local) > 2 else local[:1]
    return f"{shown}***@{domain}"


def safe_error_message(_: Exception) -> str:
    # Do not expose provider responses, SQL details, stack traces, or secrets to users/LLMs.
    return "The requested operation could not be completed safely. Please try again."


def password_matches(provided: str, expected: str) -> bool:
    if not expected:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def rate_limit_ok(timestamps: deque[float], limit: int = 15, window_seconds: int = 60) -> bool:
    now = time.time()
    while timestamps and now - timestamps[0] > window_seconds:
        timestamps.popleft()
    if len(timestamps) >= limit:
        return False
    timestamps.append(now)
    return True
