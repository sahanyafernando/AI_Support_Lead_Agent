# Security notes

This prototype includes useful hackathon-level controls, but it is not a complete production security program.

## Implemented controls

- **Secrets are server-side only.** `GROQ_API_KEY` and `SUPABASE_SECRET_KEY` are read from `.env` locally or Streamlit Secrets in deployment. `.env` and `.streamlit/secrets.toml` are gitignored.
- **Modern Supabase key model.** The app expects a `sb_secret_...` server key. A legacy `SUPABASE_SERVICE_ROLE_KEY` is accepted only as a compatibility fallback.
- **RLS + revoked client access.** The supplied SQL enables RLS and revokes table privileges from `anon` and `authenticated`. The backend secret key has elevated service-role access.
- **Tool allow-list.** The LLM can call only the tools defined in `TOOL_SCHEMAS` and `AVAILABLE_FUNCTIONS`.
- **No arbitrary SQL/code execution.** Model-provided strings are never passed to `eval()`, shell commands, or raw SQL.
- **Input validation.** Pydantic validates emails, numeric ranges, text lengths, and structured fields. Text is normalized and control characters are removed.
- **Deterministic lead scoring.** The model cannot write its own score or status. Trusted Python calculates them.
- **Runaway-loop protection.** `MAX_AGENT_STEPS` is capped at 10 and defaults to 6.
- **Basic per-session rate limiting.** Chat requests are limited in the UI to reduce accidental loops/abuse.
- **PII minimization.** Customer lookup results returned to the model use masked email addresses. Conversation persistence is disabled by default.
- **Prompt-injection boundary.** The system prompt treats user/FAQ text as untrusted and write tools still enforce validation.
- **Safe user-facing errors.** Provider/database exceptions are not sent directly to the customer or model.
- **Optional admin password.** The demo CRM dashboard can be protected with `ADMIN_PASSWORD`.

## Important limitations

1. The Supabase Secret key bypasses RLS. This is acceptable only because it lives in the Streamlit server environment. A leaked secret key can expose the project data; rotate it immediately if leaked.
2. A single shared admin password is suitable for a hackathon, not production. Use Supabase Auth/SSO and role-based authorization for a real system.
3. Streamlit session rate limiting is not a distributed WAF/rate limiter. Production deployments should add provider/API-gateway limits.
4. LLM prompt injection cannot be eliminated by prompting alone. Keep high-impact actions behind deterministic authorization/confirmation rules.
5. This demo meeting tool stores a request in Supabase. It does not create a real external appointment.
6. Do not collect payment-card information, passwords, national IDs, or unrelated sensitive data through this demo.

## Before sharing the public demo URL

- Set `ADMIN_PASSWORD` or set `ENABLE_ADMIN_DASHBOARD=false`.
- Use a dedicated Supabase project with synthetic/demo data.
- Confirm `.env` and `secrets.toml` are not in Git history.
- Keep conversation storage off unless you have a clear purpose and notice/retention policy.
- Rotate any credential that was pasted into chat, committed, screenshotted, or exposed in logs.
