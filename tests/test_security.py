from collections import deque

import pytest

from security import clean_text, mask_email, rate_limit_ok


def test_clean_text_removes_control_chars():
    assert clean_text("hello\x00world") == "helloworld"


def test_clean_text_enforces_limit():
    with pytest.raises(ValueError):
        clean_text("x" * 11, max_len=10)


def test_mask_email():
    assert mask_email("TestUser@example.com") == "te***@example.com"


def test_rate_limit():
    q = deque()
    assert rate_limit_ok(q, limit=2, window_seconds=60)
    assert rate_limit_ok(q, limit=2, window_seconds=60)
    assert not rate_limit_ok(q, limit=2, window_seconds=60)
