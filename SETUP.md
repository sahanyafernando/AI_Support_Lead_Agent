# Setup guide (Windows + VS Code, no Docker Desktop)

## 1. Create the Supabase project

1. Create a free hosted Supabase project.
2. Open **SQL Editor**.
3. Copy all of `supabase/schema.sql`, run it once, and verify the five tables exist.
4. Open the project's **Connect** dialog or **Settings > API Keys**.
5. Copy:
   - Project URL -> `SUPABASE_URL`
   - A server-side **Secret key** beginning `sb_secret_...` -> `SUPABASE_SECRET_KEY`

Do not use the secret key in browser-side JavaScript and never commit it.

## 2. Create a Groq key

Create a Groq API key and copy it as `GROQ_API_KEY`.

## 3. Open the project in VS Code

PowerShell:

```powershell
cd path\to\ai_support_lead_agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Add your keys

Edit `.env`:

```env
GROQ_API_KEY=your_real_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=sb_secret_your_real_key
```

Optional for a public demo:

```env
ADMIN_PASSWORD=choose-a-strong-demo-password
```

## 5. Check the database

```powershell
python scripts/check_setup.py
```

Expected ending:

```text
Supabase schema connection: OK
Setup looks ready.
```

## 6. Run tests

```powershell
pytest -q
```

## 7. Run the app

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit.

## 8. Demo script

Try this sequence:

```text
What AI services do you provide?
```

Then:

```text
I want an AI support agent for my software company. We have about 80 employees and want to deploy in a month.
```

When asked, provide a fake hackathon identity/email and say:

```text
Our approximate budget is $15,000 and I am the decision maker. Please add me as a lead.
```

Then:

```text
I'd like a meeting next Friday afternoon.
```

Open **Agent Activity** and **CRM Dashboard** so judges can see actual tool calls and stored records.

## 9. Deploy to Streamlit Community Cloud

1. Push the repository to GitHub. Confirm `.env` is not included.
2. In Streamlit Community Cloud, create an app from the repository and set `app.py` as the entrypoint.
3. In the app's Secrets/Advanced settings, add values equivalent to:

```toml
GROQ_API_KEY = "..."
SUPABASE_URL = "https://...supabase.co"
SUPABASE_SECRET_KEY = "sb_secret_..."
GROQ_MODEL = "llama-3.3-70b-versatile"
ENABLE_ADMIN_DASHBOARD = "true"
ADMIN_PASSWORD = "..."
```

4. Deploy and retest the full demo flow.

No Docker Desktop is required in this workflow.
