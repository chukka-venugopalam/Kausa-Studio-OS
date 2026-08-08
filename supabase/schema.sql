-- Kausa Studio OS — Core Schema
-- Multi-tenant from day one: every content table carries brand_id,
-- even though only one brand exists today. Adding brand #2 later means
-- inserting a row, not migrating a schema. This is the entire technical
-- answer to "capable of running dozens in the future."

create extension if not exists pgcrypto;

create table brands (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  style_bible_version text not null default 'v1.0',
  created_at timestamptz not null default now()
);

create table series (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references brands(id),
  name text not null,
  domain_color text not null,
  description text,
  created_at timestamptz not null default now(),
  unique (brand_id, name)
);

-- The Research Bible's structured dataset, and the sellable IP asset
-- from the monetization plan. sources is a JSON array of {type, url_or_ref}.
create table chains (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references brands(id),
  series_id uuid references series(id),
  hook_text text not null,
  node_1 text not null,
  node_2 text not null,
  payoff text not null,
  sources jsonb not null default '[]',
  confidence_level text check (confidence_level in ('high','medium','low')),
  verification_status text not null default 'pending'
    check (verification_status in ('pending','verified','rejected')),
  credited_suggester text,
  created_at timestamptz not null default now(),
  verified_at timestamptz,
  verified_by text
);

-- The knowledge graph edges. This table, populated over years, is what
-- makes Lume's callbacks accurate instead of just a character trait
-- the show claims to have.
create table chain_links (
  id uuid primary key default gen_random_uuid(),
  chain_id uuid not null references chains(id),
  related_chain_id uuid not null references chains(id),
  link_type text not null default 'related',
  created_at timestamptz not null default now(),
  check (chain_id <> related_chain_id)
);

-- The working-memory state machine: one row per episode, so any
-- workflow can pick up exactly where the last one left off.
create table productions (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references brands(id),
  chain_id uuid references chains(id),
  season_number int not null,
  episode_number int not null,
  status text not null default 'idea' check (status in (
    'idea','researching','verified','scripted','assets_ready',
    'edited','published','archived','failed'
  )),
  script_text text,
  veo3_prompt text,
  last_error text,
  current_step_started_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (brand_id, season_number, episode_number)
);

create table episodes (
  id uuid primary key default gen_random_uuid(),
  production_id uuid not null references productions(id),
  youtube_url text,
  instagram_url text,
  title text not null,
  description text,
  published_at timestamptz
);

create table analytics_snapshots (
  id uuid primary key default gen_random_uuid(),
  episode_id uuid not null references episodes(id),
  platform text not null check (platform in ('youtube','instagram')),
  pulled_at timestamptz not null default now(),
  ctr numeric,
  retention_3s numeric,
  avg_view_duration_pct numeric,
  shares int,
  saves int,
  comments int,
  subscriber_delta int
);

create table experiments (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references brands(id),
  started_at timestamptz not null default now(),
  variable_tested text not null,
  hypothesis text,
  result_summary text,
  winner boolean,
  adopted boolean not null default false
);

create table contributors (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references brands(id),
  platform_username text not null,
  credited_chain_count int not null default 0,
  tier text not null default 'new' check (tier in ('new','repeat','moderator')),
  unique (brand_id, platform_username)
);

-- Audit log for every automated run. This is the backbone of the
-- failure-recovery design in ARCHITECTURE.md -- a crashed run always
-- leaves an inspectable row here, never a silent gap.
create table agent_runs (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references brands(id),
  agent_name text not null,
  production_id uuid references productions(id),
  status text not null check (status in ('running','success','failed')),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  error_message text,
  github_run_id text
);

-- Deliberately trivial table. A scheduled GitHub Action writes one row
-- here every few days purely to keep the free-tier Supabase project
-- from auto-pausing after 7 days of no API activity.
create table keepalive_pings (
  id bigint generated always as identity primary key,
  pinged_at timestamptz not null default now()
);

create index idx_chains_brand_status on chains(brand_id, verification_status);
create index idx_productions_brand_status on productions(brand_id, status);
create index idx_agent_runs_status on agent_runs(status, started_at);
