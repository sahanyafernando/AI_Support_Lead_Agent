from __future__ import annotations

import json
import re
from typing import Any, Callable

from pydantic import ValidationError

import database
from lead_scoring import calculate_lead_score as score_lead
from models import CustomerInput, LeadInput, MeetingInput
from security import clean_text, mask_email, safe_error_message

STOP_WORDS = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "is", "are",
    "do", "does", "what", "how", "can", "i", "we", "you", "your", "our", "with",
}


def _keywords(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 3 and token not in STOP_WORDS
    }


def search_knowledge_base(query: str) -> dict[str, Any]:
    query = clean_text(query, 300, allow_newlines=False)
    rows = database.list_faqs(limit=100)
    qwords = _keywords(query)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for row in rows:
        haystack = f"{row.get('question', '')} {row.get('answer', '')} {row.get('category', '')}"
        score = len(qwords & _keywords(haystack))
        if score > 0:
            ranked.append((score, row))
    ranked.sort(key=lambda item: item[0], reverse=True)
    results = [item[1] for item in ranked[:5]]
    return {"success": True, "results": results}


def check_customer(email: str) -> dict[str, Any]:
    try:
        model = CustomerInput(name="Lookup", email=email)
        customer = database.find_customer(str(model.email))
        if not customer:
            return {"success": True, "exists": False, "email": mask_email(str(model.email))}
        # Never return the full record to the model; only minimal context.
        return {
            "success": True,
            "exists": True,
            "customer_id": customer["id"],
            "name": customer["name"],
            "company": customer.get("company"),
            "email": mask_email(customer["email"]),
        }
    except (ValidationError, ValueError):
        return {"success": False, "error": "Please provide a valid email address."}
    except Exception as exc:
        return {"success": False, "error": safe_error_message(exc)}


def create_customer(name: str, email: str, company: str | None = None, phone: str | None = None) -> dict[str, Any]:
    try:
        model = CustomerInput(name=name, email=email, company=company, phone=phone)
        normalized_email = str(model.email)
        existing = database.find_customer(normalized_email)
        if existing:
            return {
                "success": True,
                "created": False,
                "customer_id": existing["id"],
                "name": existing["name"],
                "email": mask_email(existing["email"]),
            }
        created = database.insert_customer(model.model_dump(mode="json"))
        return {
            "success": True,
            "created": True,
            "customer_id": created["id"],
            "name": created["name"],
            "email": mask_email(created["email"]),
        }
    except (ValidationError, ValueError) as exc:
        return {"success": False, "error": f"Invalid customer information: {exc}"}
    except Exception as exc:
        return {"success": False, "error": safe_error_message(exc)}


def calculate_lead_score(
    company_size: int | None = None,
    budget_usd: float | None = None,
    timeline_days: int | None = None,
    decision_maker: bool | None = None,
) -> dict[str, Any]:
    try:
        # Reuse the LeadInput numeric constraints without needing real contact data.
        if company_size is not None and not (1 <= int(company_size) <= 1_000_000):
            raise ValueError("company_size out of range")
        if budget_usd is not None and not (0 <= float(budget_usd) <= 1_000_000_000):
            raise ValueError("budget_usd out of range")
        if timeline_days is not None and not (1 <= int(timeline_days) <= 3650):
            raise ValueError("timeline_days out of range")
        result = score_lead(company_size, budget_usd, timeline_days, decision_maker)
        return {"success": True, **result.to_dict()}
    except (TypeError, ValueError):
        return {"success": False, "error": "Invalid qualification values."}


def create_lead(
    email: str,
    requirement: str,
    company_size: int | None = None,
    budget_usd: float | None = None,
    timeline_days: int | None = None,
    decision_maker: bool | None = None,
) -> dict[str, Any]:
    try:
        model = LeadInput(
            email=email,
            requirement=requirement,
            company_size=company_size,
            budget_usd=budget_usd,
            timeline_days=timeline_days,
            decision_maker=decision_maker,
        )
        customer = database.find_customer(str(model.email))
        if not customer:
            return {
                "success": False,
                "error": "Customer not found. Create the customer first with create_customer.",
            }
        score = score_lead(model.company_size, model.budget_usd, model.timeline_days, model.decision_maker)
        payload = {
            "customer_id": customer["id"],
            "company_size": model.company_size,
            "budget_usd": model.budget_usd,
            "timeline_days": model.timeline_days,
            "decision_maker": model.decision_maker,
            "requirement": model.requirement,
            "score": score.score,
            "status": score.status,
            "qualification_reasons": score.reasons,
        }
        if score.score < 35:
            return {
                "success": True,
                "qualified": False,
                "lead_id": None,
                "score": score.score,
                "status": score.status,
                "reasons": score.reasons,
                "message": "Lead is not qualified yet, so it was not inserted into the CRM leads table.",
            }
        lead = database.insert_lead(payload)
        return {
            "success": True,
            "qualified": True,
            "lead_id": lead["id"],
            "score": lead["score"],
            "status": lead["status"],
            "reasons": lead.get("qualification_reasons") or [],
        }
    except (ValidationError, ValueError) as exc:
        return {"success": False, "error": f"Invalid lead information: {exc}"}
    except Exception as exc:
        return {"success": False, "error": safe_error_message(exc)}


def schedule_meeting(email: str, preferred_time: str, notes: str | None = None) -> dict[str, Any]:
    try:
        model = MeetingInput(email=email, preferred_time=preferred_time, notes=notes)
        customer = database.find_customer(str(model.email))
        if not customer:
            return {"success": False, "error": "Customer not found. Create the customer first."}
        meeting = database.insert_meeting(
            {
                "customer_id": customer["id"],
                "preferred_time": model.preferred_time,
                "notes": model.notes,
                "status": "REQUESTED",
            }
        )
        return {
            "success": True,
            "meeting_id": meeting["id"],
            "status": meeting["status"],
            "preferred_time": meeting["preferred_time"],
            "message": "Meeting request saved in CRM; external calendar confirmation is not implemented.",
        }
    except (ValidationError, ValueError) as exc:
        return {"success": False, "error": f"Invalid meeting information: {exc}"}
    except Exception as exc:
        return {"success": False, "error": safe_error_message(exc)}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search company FAQ/knowledge-base content before answering questions about services, pricing, support, implementation, integrations, or policies.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Short factual search query."}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_customer",
            "description": "Check whether the current user-provided email already exists as a customer. Never use this to enumerate customers.",
            "parameters": {
                "type": "object",
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_customer",
            "description": "Create a customer record after the user has voluntarily provided contact details and shown support or buying intent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "company": {"type": "string"},
                    "phone": {"type": "string"},
                },
                "required": ["name", "email"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_lead_score",
            "description": "Calculate the deterministic lead score from known qualification fields. Unknown fields should be omitted, never guessed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_size": {"type": "integer"},
                    "budget_usd": {"type": "number"},
                    "timeline_days": {"type": "integer"},
                    "decision_maker": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_lead",
            "description": "Create a CRM lead for an existing customer. Score/status are calculated by trusted application logic and must not be supplied by the model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "requirement": {"type": "string"},
                    "company_size": {"type": "integer"},
                    "budget_usd": {"type": "number"},
                    "timeline_days": {"type": "integer"},
                    "decision_maker": {"type": "boolean"},
                },
                "required": ["email", "requirement"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Store a meeting request in the CRM after the user asks for one. This demo does not create a real Google/Microsoft calendar event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "preferred_time": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["email", "preferred_time"],
                "additionalProperties": False,
            },
        },
    },
]

AVAILABLE_FUNCTIONS: dict[str, Callable[..., dict[str, Any]]] = {
    "search_knowledge_base": search_knowledge_base,
    "check_customer": check_customer,
    "create_customer": create_customer,
    "calculate_lead_score": calculate_lead_score,
    "create_lead": create_lead,
    "schedule_meeting": schedule_meeting,
}


def execute_tool_call(tool_call) -> tuple[str, dict[str, Any]]:
    name = tool_call.function.name
    if name not in AVAILABLE_FUNCTIONS:
        return name, {"success": False, "error": "Tool is not allowed."}
    try:
        args = json.loads(tool_call.function.arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError("Tool arguments must be an object.")
    except (json.JSONDecodeError, ValueError):
        return name, {"success": False, "error": "Invalid tool arguments."}
    try:
        return name, AVAILABLE_FUNCTIONS[name](**args)
    except TypeError:
        return name, {"success": False, "error": "Invalid or unexpected tool parameters."}
