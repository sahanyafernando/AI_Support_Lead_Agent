from __future__ import annotations

from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from config import get_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError("Supabase configuration is missing.")
    # This is a server-side secret key. Never send it to browser/client code.
    return create_client(settings.supabase_url, settings.supabase_secret_key)


def health_check() -> bool:
    get_supabase().table("faqs").select("id").limit(1).execute()
    return True


def list_faqs(limit: int = 100) -> list[dict[str, Any]]:
    response = (
        get_supabase()
        .table("faqs")
        .select("id,question,answer,category")
        .limit(max(1, min(limit, 200)))
        .execute()
    )
    return response.data or []


def find_customer(email: str) -> dict[str, Any] | None:
    response = (
        get_supabase()
        .table("customers")
        .select("id,name,email,company,phone,created_at")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return (response.data or [None])[0]


def insert_customer(data: dict[str, Any]) -> dict[str, Any]:
    response = (
        get_supabase()
        .table("customers")
        .insert(data)
        .select("id,name,email,company,phone,created_at")
        .execute()
    )
    return response.data[0]


def insert_lead(data: dict[str, Any]) -> dict[str, Any]:
    response = (
        get_supabase()
        .table("leads")
        .insert(data)
        .select("id,customer_id,company_size,budget_usd,timeline_days,decision_maker,requirement,score,status,qualification_reasons,created_at")
        .execute()
    )
    return response.data[0]


def insert_meeting(data: dict[str, Any]) -> dict[str, Any]:
    response = (
        get_supabase()
        .table("meetings")
        .insert(data)
        .select("id,customer_id,preferred_time,notes,status,created_at")
        .execute()
    )
    return response.data[0]


def insert_conversation(data: dict[str, Any]) -> None:
    get_supabase().table("conversations").insert(data).execute()


def list_recent_leads(limit: int = 20) -> list[dict[str, Any]]:
    response = (
        get_supabase()
        .table("leads")
        .select("id,customer_id,company_size,budget_usd,timeline_days,decision_maker,requirement,score,status,created_at,customers(name,email,company)")
        .order("created_at", desc=True)
        .limit(max(1, min(limit, 100)))
        .execute()
    )
    return response.data or []


def list_recent_meetings(limit: int = 20) -> list[dict[str, Any]]:
    response = (
        get_supabase()
        .table("meetings")
        .select("id,customer_id,preferred_time,notes,status,created_at,customers(name,email,company)")
        .order("created_at", desc=True)
        .limit(max(1, min(limit, 100)))
        .execute()
    )
    return response.data or []
