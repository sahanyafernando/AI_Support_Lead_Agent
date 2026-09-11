from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _secret(name: str, default: str | None = None) -> str | None:
    """Read from environment first, then Streamlit secrets if available."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        if name in st.secrets:
            raw = st.secrets[name]
            return str(raw) if raw is not None else default
    except Exception:
        pass
    return default


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    supabase_url: str
    supabase_secret_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    max_agent_steps: int = 6
    max_user_message_chars: int = 2500
    store_conversations: bool = False
    enable_admin_dashboard: bool = True
    admin_password: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        groq_api_key=_secret("GROQ_API_KEY", "") or "",
        supabase_url=_secret("SUPABASE_URL", "") or "",
        supabase_secret_key=(
            _secret("SUPABASE_SECRET_KEY", "")
            or _secret("SUPABASE_SERVICE_ROLE_KEY", "")
            or ""
        ),
        groq_model=_secret("GROQ_MODEL", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile",
        max_agent_steps=max(1, min(int(_secret("MAX_AGENT_STEPS", "6") or 6), 10)),
        max_user_message_chars=max(500, min(int(_secret("MAX_USER_MESSAGE_CHARS", "2500") or 2500), 8000)),
        store_conversations=_as_bool(_secret("STORE_CONVERSATIONS", "false"), False),
        enable_admin_dashboard=_as_bool(_secret("ENABLE_ADMIN_DASHBOARD", "true"), True),
        admin_password=_secret("ADMIN_PASSWORD", "") or "",
    )


def missing_required_settings() -> list[str]:
    settings = get_settings()
    missing: list[str] = []
    if not settings.groq_api_key:
        missing.append("GROQ_API_KEY")
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.supabase_secret_key:
        missing.append("SUPABASE_SECRET_KEY")
    return missing
