-- AI Support / Lead Qualification Agent
-- Run this once in Supabase -> SQL Editor.
-- Designed for server-side access through SUPABASE_SECRET_KEY.

create extension if not exists pgcrypto;

create table if not exists public.faqs (
    id uuid primary key default gen_random_uuid(),
    question text not null unique,
    answer text not null,
    category text not null default 'general',
    created_at timestamptz not null default now()
);

create table if not exists public.customers (
    id uuid primary key default gen_random_uuid(),
    name text not null check (char_length(name) between 1 and 80),
    email text not null unique check (char_length(email) <= 254),
    company text check (company is null or char_length(company) <= 120),
    phone text check (phone is null or char_length(phone) <= 30),
    created_at timestamptz not null default now()
);

create table if not exists public.leads (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid not null references public.customers(id) on delete cascade,
    company_size integer check (company_size is null or company_size between 1 and 1000000),
    budget_usd numeric(14,2) check (budget_usd is null or budget_usd between 0 and 1000000000),
    timeline_days integer check (timeline_days is null or timeline_days between 1 and 3650),
    decision_maker boolean,
    requirement text not null check (char_length(requirement) between 3 and 1000),
    score integer not null check (score between 0 and 100),
    status text not null check (status in ('HOT','WARM','COLD')),
    qualification_reasons jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.meetings (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid not null references public.customers(id) on delete cascade,
    preferred_time text not null check (char_length(preferred_time) between 2 and 120),
    notes text check (notes is null or char_length(notes) <= 500),
    status text not null default 'REQUESTED' check (status in ('REQUESTED','CONFIRMED','CANCELLED')),
    created_at timestamptz not null default now()
);

create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),
    session_id text not null check (char_length(session_id) <= 64),
    role text not null check (role in ('user','assistant')),
    content text not null check (char_length(content) <= 8000),
    created_at timestamptz not null default now()
);

create index if not exists idx_leads_customer_id on public.leads(customer_id);
create index if not exists idx_leads_created_at on public.leads(created_at desc);
create index if not exists idx_leads_status on public.leads(status);
create index if not exists idx_meetings_customer_id on public.meetings(customer_id);
create index if not exists idx_meetings_created_at on public.meetings(created_at desc);
create index if not exists idx_conversations_session on public.conversations(session_id, created_at);

-- Defense in depth: client roles get no table access in this prototype.
-- The Streamlit server uses a Supabase Secret key (service_role privileges).
alter table public.faqs enable row level security;
alter table public.customers enable row level security;
alter table public.leads enable row level security;
alter table public.meetings enable row level security;
alter table public.conversations enable row level security;

revoke all on table public.faqs from anon, authenticated;
revoke all on table public.customers from anon, authenticated;
revoke all on table public.leads from anon, authenticated;
revoke all on table public.meetings from anon, authenticated;
revoke all on table public.conversations from anon, authenticated;

grant usage on schema public to service_role;
grant all on table public.faqs to service_role;
grant all on table public.customers to service_role;
grant all on table public.leads to service_role;
grant all on table public.meetings to service_role;
grant all on table public.conversations to service_role;

-- Seed demo knowledge. Replace these rows with the hackathon company's real FAQs.
insert into public.faqs (question, answer, category) values
('What services do you provide?', 'We provide AI customer-support agents, lead qualification automation, workflow automation, and custom AI integrations.', 'services'),
('Can your AI agents work 24/7?', 'Yes. AI agents can be configured to handle customer conversations continuously, with escalation paths for cases that need a human.', 'support'),
('Do you integrate with CRM systems?', 'CRM integrations can be implemented through APIs and webhooks. The exact supported systems depend on the project requirements.', 'integrations'),
('Can the agent qualify sales leads?', 'Yes. The agent can collect qualification information and apply configurable business rules to classify leads before sending them to a CRM.', 'sales'),
('Can I speak to a human?', 'Yes. A production solution can include human handoff when the user requests it or when the AI cannot safely resolve the issue.', 'support'),
('How long does implementation take?', 'Implementation time depends on integrations, knowledge-base size, testing requirements, and workflow complexity. A discovery call is used to estimate a project accurately.', 'implementation'),
('How much does it cost?', 'Pricing depends on conversation volume, integrations, channels, and customization. The team provides a tailored quote after learning the requirements.', 'pricing'),
('Do you support voice agents?', 'Voice-agent solutions can support inbound customer conversations, FAQ handling, qualification, and routing when integrated with telephony and speech services.', 'voice')
on conflict (question) do update set
    answer = excluded.answer,
    category = excluded.category;
