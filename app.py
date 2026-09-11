from __future__ import annotations

import uuid
from collections import deque

import streamlit as st

import database
from agent import run_agent
from config import get_settings, missing_required_settings
from security import password_matches, rate_limit_ok

st.set_page_config(
    page_title="AI Support & Lead Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
.hero {padding: 1.2rem 1.4rem; border: 1px solid rgba(255,255,255,.10); border-radius: 18px; margin-bottom: 1rem;}
.hero h1 {margin: 0 0 .25rem 0; font-size: 2rem;}
.hero p {margin: 0; opacity: .78;}
.pill {display:inline-block; padding:.22rem .55rem; border-radius:999px; border:1px solid rgba(255,255,255,.16); font-size:.78rem; margin-right:.3rem;}
.small {font-size:.84rem; opacity:.72;}
</style>
""",
    unsafe_allow_html=True,
)

settings = get_settings()
missing = missing_required_settings()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I can answer questions about our AI services, understand your requirements, and create a qualified CRM lead or meeting request. How can I help?",
        }
    ]
if "activities" not in st.session_state:
    st.session_state.activities = []
if "message_times" not in st.session_state:
    st.session_state.message_times = deque()
if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False

st.markdown(
    """
<div class="hero">
  <h1>🤖 AI Support + Lead Qualification Agent</h1>
  <p>FAQ support → customer capture → deterministic qualification → CRM lead → meeting request</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Demo status")
    st.caption(f"Model: `{settings.groq_model}`")
    if missing:
        st.error("Missing configuration: " + ", ".join(missing))
    else:
        st.success("Secrets loaded")

    if st.button("Test Supabase connection", use_container_width=True, disabled=bool(missing)):
        try:
            database.health_check()
            st.success("Supabase connected")
        except Exception:
            st.error("Database connection failed. Check URL/key and run supabase/schema.sql.")

    st.divider()
    st.caption("Agent capabilities")
    st.markdown(
        "<span class='pill'>Knowledge</span><span class='pill'>CRM</span><span class='pill'>Lead score</span><span class='pill'>Meeting</span>",
        unsafe_allow_html=True,
    )
    st.caption("This demo stores a meeting request; it does not create a real calendar event.")

chat_tab, activity_tab, crm_tab, architecture_tab = st.tabs(
    ["💬 Customer Chat", "⚙️ Agent Activity", "📈 CRM Dashboard", "🧩 Architecture"]
)

with chat_tab:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask a support question or describe what your company needs…", disabled=bool(missing))
    if prompt:
        if not rate_limit_ok(st.session_state.message_times, limit=15, window_seconds=60):
            st.warning("Too many messages in a short period. Please wait briefly and try again.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            try:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking and checking tools…"):
                        reply, activities = run_agent(
                            user_message=prompt,
                            history=st.session_state.messages[:-1],
                            session_id=st.session_state.session_id,
                        )
                    st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.session_state.activities.extend(activities)
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("The agent request failed safely. Check your API configuration and terminal logs.")

with activity_tab:
    st.subheader("What makes this an agent, not only a chatbot")
    st.caption("The model can choose allowed tools, your Python code executes them, and results return to the model. Sensitive raw tool output is not displayed here.")
    if not st.session_state.activities:
        st.info("No tools have been called in this session yet. Ask about services or tell the agent you are interested in buying.")
    else:
        for item in reversed(st.session_state.activities[-30:]):
            icon = "✅" if item.get("success") else "⚠️"
            details = {k: v for k, v in item.items() if k not in {"tool", "success"}}
            st.markdown(f"**{icon} `{item['tool']}`**")
            if details:
                st.json(details, expanded=False)

with crm_tab:
    if not settings.enable_admin_dashboard:
        st.info("Admin dashboard is disabled by configuration.")
    else:
        if settings.admin_password and not st.session_state.admin_ok:
            st.warning("Admin dashboard is protected.")
            entered = st.text_input("Admin password", type="password")
            if st.button("Unlock dashboard"):
                if password_matches(entered, settings.admin_password):
                    st.session_state.admin_ok = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            if not settings.admin_password:
                st.warning("Demo mode: ADMIN_PASSWORD is not set. Set one before sharing a public URL.")
            if missing:
                st.info("Configure Supabase to view CRM data.")
            else:
                try:
                    leads = database.list_recent_leads(25)
                    meetings = database.list_recent_meetings(25)
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Recent leads", len(leads))
                    c2.metric("🔥 Hot", sum(1 for x in leads if x.get("status") == "HOT"))
                    c3.metric("🟡 Warm", sum(1 for x in leads if x.get("status") == "WARM"))
                    c4.metric("Meeting requests", len(meetings))

                    st.subheader("Recent leads")
                    if leads:
                        display = []
                        for lead in leads:
                            customer = lead.get("customers") or {}
                            display.append(
                                {
                                    "name": customer.get("name"),
                                    "company": customer.get("company"),
                                    "email": customer.get("email"),
                                    "score": lead.get("score"),
                                    "status": lead.get("status"),
                                    "requirement": lead.get("requirement"),
                                    "created_at": lead.get("created_at"),
                                }
                            )
                        st.dataframe(display, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No leads yet.")

                    st.subheader("Meeting requests")
                    if meetings:
                        display_meetings = []
                        for meeting in meetings:
                            customer = meeting.get("customers") or {}
                            display_meetings.append(
                                {
                                    "name": customer.get("name"),
                                    "company": customer.get("company"),
                                    "preferred_time": meeting.get("preferred_time"),
                                    "status": meeting.get("status"),
                                    "created_at": meeting.get("created_at"),
                                }
                            )
                        st.dataframe(display_meetings, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No meeting requests yet.")
                except Exception:
                    st.error("Unable to load CRM dashboard. Verify the Supabase schema and key.")

with architecture_tab:
    st.subheader("Architecture")
    st.code(
        """
Customer
   │
   ▼
Streamlit UI
   │
   ▼
Groq LLM Agent ─── local tool-calling loop
   │
   ├── search_knowledge_base() ──► Supabase FAQs
   ├── check_customer() ─────────► Supabase Customers
   ├── create_customer() ────────► Supabase Customers
   ├── calculate_lead_score() ───► Deterministic Python rules
   ├── create_lead() ────────────► Supabase Leads (CRM simulation)
   └── schedule_meeting() ───────► Supabase Meeting Requests
        """.strip(),
        language="text",
    )
    st.markdown(
        """
**Security boundary:** the browser talks only to Streamlit. Groq and Supabase secret keys remain in the Streamlit server environment. The Supabase secret key bypasses RLS, so it is intentionally never sent to client-side code and should be rotated immediately if leaked.

**Lead qualification:** the LLM gathers data, but Python business rules calculate the score. This makes the HOT/WARM/COLD decision auditable and prevents the model from fabricating a score.
        """
    )
