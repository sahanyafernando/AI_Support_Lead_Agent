from __future__ import annotations

import json
from typing import Any

from groq import Groq

import database
from config import get_settings
from prompts import SYSTEM_PROMPT
from security import clean_text
from tools import TOOL_SCHEMAS, execute_tool_call


def _history_messages(history: list[dict[str, str]], max_messages: int = 12) -> list[dict[str, str]]:
    clean: list[dict[str, str]] = []
    for item in history[-max_messages:]:
        role = item.get("role")
        content = item.get("content", "")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        clean.append({"role": role, "content": clean_text(content, 4000)})
    return clean


def _activity_summary(name: str, result: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"tool": name, "success": bool(result.get("success"))}
    for field in ("created", "exists", "qualified", "status", "score", "preferred_time"):
        if field in result:
            summary[field] = result[field]
    if not result.get("success"):
        summary["message"] = result.get("error", "Tool failed")
    return summary


def run_agent(
    user_message: str,
    history: list[dict[str, str]],
    session_id: str,
) -> tuple[str, list[dict[str, Any]]]:
    settings = get_settings()
    user_message = clean_text(user_message, settings.max_user_message_chars)
    client = Groq(api_key=settings.groq_api_key, timeout=30.0)

    messages: list[Any] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(_history_messages(history))
    messages.append({"role": "user", "content": user_message})

    activities: list[dict[str, Any]] = []

    for _ in range(settings.max_agent_steps):
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
            max_completion_tokens=900,
        )
        response_message = response.choices[0].message
        messages.append(response_message)
        tool_calls = response_message.tool_calls or []

        if not tool_calls:
            content = (response_message.content or "").strip()
            if not content:
                content = "I couldn't produce a response. Please rephrase your request."
            if settings.store_conversations:
                try:
                    database.insert_conversation(
                        {"session_id": session_id, "role": "user", "content": user_message}
                    )
                    database.insert_conversation(
                        {"session_id": session_id, "role": "assistant", "content": content}
                    )
                except Exception:
                    # Conversation logging is optional; never fail the customer interaction because logging failed.
                    pass
            return content, activities

        for tool_call in tool_calls:
            name, result = execute_tool_call(tool_call)
            activities.append(_activity_summary(name, result))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )

    # Guard against runaway agent loops and unexpected tool-chaining.
    messages.append(
        {
            "role": "system",
            "content": "Tool-step limit reached. Do not call more tools. Briefly summarize what was completed and what information is still needed.",
        }
    )
    final = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.2,
        max_completion_tokens=600,
    )
    return (final.choices[0].message.content or "Agent step limit reached."), activities
