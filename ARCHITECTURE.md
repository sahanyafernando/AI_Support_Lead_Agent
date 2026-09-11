# Architecture

```text
Customer
   |
   v
Streamlit UI
   |
   v
Groq LLM Agent
   |
   +--> search_knowledge_base() --> Supabase: faqs
   +--> check_customer() --------> Supabase: customers
   +--> create_customer() -------> Supabase: customers
   +--> calculate_lead_score() --> trusted Python rules
   +--> create_lead() -----------> Supabase: leads
   +--> schedule_meeting() ------> Supabase: meetings
```

## Why this is an agent

A chatbot can generate text. This application can select from explicitly allowed tools, pass structured arguments, execute application/database operations, inspect the result, and continue reasoning toward the user's goal.

## Request flow

1. User enters a message in Streamlit.
2. Streamlit sends the current message plus a limited recent history to Groq.
3. Groq may return one or more local tool calls.
4. Python validates the tool name and arguments and executes only allow-listed functions.
5. Tool results return to Groq.
6. The loop stops when Groq returns a normal answer or when the configured step limit is reached.
7. Only CRM/FAQ data needed by the operation is read/written in Supabase.

## Trust boundaries

- Browser: untrusted. It never receives Groq or Supabase secret keys.
- Streamlit server: trusted application layer. It holds secrets and executes tools.
- LLM: untrusted decision-maker for text/tool selection. It cannot execute arbitrary Python or SQL.
- Tool layer: trusted enforcement layer. It validates inputs and calculates scores.
- Supabase: persistent data store/CRM simulation.

## Production extensions

- Add Supabase Auth or SSO for staff dashboards.
- Replace the meeting-request tool with Google Calendar / Microsoft Graph.
- Replace FAQ keyword ranking with embeddings + pgvector for larger corpora.
- Add a real CRM connector (HubSpot/Salesforce).
- Add speech-to-text and text-to-speech around the same agent core.
