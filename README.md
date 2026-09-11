# AI Support + Lead Qualification Agent

A fast, cloud-first hackathon project built with **Streamlit + Groq + Supabase**. It answers FAQs, captures customers, qualifies leads using deterministic business rules, writes qualified leads to a Supabase-backed CRM simulation, and records meeting requests.

## Why this is more than a chatbot

The LLM does not only generate replies. It can select explicitly allowed tools, call them with structured arguments, read their results, and continue toward a customer-support or lead-qualification goal.

```text
Customer
   |
   v
Streamlit
   |
   v
Groq LLM Agent
   |
   +--> Knowledge Base ------> Supabase faqs
   +--> Customer operations -> Supabase customers
   +--> Lead scoring --------> deterministic Python rules
   +--> CRM lead ------------> Supabase leads
   +--> Meeting request -----> Supabase meetings
```

## Features

- Streamlit chat UI and judge-friendly agent activity view
- Groq local function/tool calling with a capped agent loop
- FAQ knowledge search
- Customer lookup/create
- Deterministic 0-100 HOT/WARM/COLD lead scoring
- CRM lead creation in Supabase
- Meeting-request capture
- Optional conversation persistence (off by default)
- Admin CRM dashboard with optional password
- Input validation, secret isolation, tool allow-list, safe error handling, PII minimization, rate limiting, and RLS defense-in-depth
- Pytest tests
- No Docker Desktop required

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run `supabase/schema.sql` in the Supabase SQL Editor, then add your keys to `.env`:

```env
GROQ_API_KEY=...
SUPABASE_URL=https://....supabase.co
SUPABASE_SECRET_KEY=sb_secret_...
ADMIN_PASSWORD=optional-demo-password
```

Then:

```powershell
python scripts/check_setup.py
pytest -q
streamlit run app.py
```

Full instructions: **SETUP.md**  
Architecture and trust boundaries: **ARCHITECTURE.md**  
Security review: **SECURITY.md**

## Project structure

```text
ai_support_lead_agent/
├── app.py                  # Streamlit UI
├── agent.py                # Groq tool-calling orchestration
├── tools.py                # Agent tool schemas + implementations
├── database.py             # Supabase data access
├── lead_scoring.py         # Trusted deterministic qualification logic
├── models.py               # Pydantic validation
├── security.py             # Sanitization, masking, rate-limit helpers
├── prompts.py              # Agent instructions
├── config.py               # Environment/Streamlit secret loading
├── requirements.txt
├── .env.example
├── .gitignore
├── .streamlit/config.toml
├── supabase/schema.sql
├── sample_data/faqs.csv
├── scripts/check_setup.py
├── tests/
├── SETUP.md
├── ARCHITECTURE.md
└── SECURITY.md
```

## Lead scoring

The LLM never decides the score directly.

| Signal | Rule | Points |
|---|---|---:|
| Company size | 1-10 / 11-50 / 51-199 / 200+ | 5 / 15 / 25 / 30 |
| Budget | below $1k / $1k-$9,999 / $10k+ | 5 / 20 / 30 |
| Timeline | >90d / <=90d / <=30d | 5 / 15 / 25 |
| Decision maker | yes | 15 |

- `60+` = HOT
- `35-59` = WARM
- `<35` = COLD (not inserted into the qualified `leads` table)

Change these rules in `lead_scoring.py` to match the challenge company.

## Security model

The browser never receives your Groq or Supabase secret key. Streamlit is the server-side application layer and calls both services. The supplied database SQL removes direct `anon`/`authenticated` table privileges. See `SECURITY.md` before deploying publicly.

> Important: Supabase's `sb_secret_...` key has elevated access and bypasses RLS. Keep it only in `.env`/Streamlit Secrets and rotate it if exposed.

## Meeting integration

`schedule_meeting()` intentionally stores a meeting **request** in Supabase. It does not pretend to create a real Google/Microsoft calendar event. For a real hackathon extension, swap that tool implementation for an actual calendar API while keeping the same agent architecture.

## Groq model

Default:

```env
GROQ_MODEL=llama-3.3-70b-versatile
```

You can change this without modifying code as long as the selected Groq-hosted model supports local tool calling.
