-- ============================================================
-- WC2026 Predictor — Supabase Schema
-- Run this entire file in the Supabase SQL Editor
-- ============================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";


-- ─── USERS ───────────────────────────────────────────────────────────────────
create table if not exists users (
  id               uuid primary key default uuid_generate_v4(),
  name             text not null,
  phone_number     text not null unique,
  total_points     integer not null default 0,
  weekly_points    integer not null default 0,
  exact_predictions integer not null default 0,
  is_admin         boolean not null default false,
  is_banned        boolean not null default false,
  created_at       timestamptz not null default now()
);

create index if not exists idx_users_phone on users(phone_number);


-- ─── MATCHES ─────────────────────────────────────────────────────────────────
create table if not exists matches (
  id                   uuid primary key default uuid_generate_v4(),
  team1                text not null,
  team2                text not null,
  kickoff_time         timestamptz not null,
  stage                text not null check (stage in ('Group','Round of 16','Quarter Final','Semi Final','Final')),
  status               text not null default 'upcoming' check (status in ('upcoming','live','completed')),
  actual_team1_score   integer,
  actual_team2_score   integer,
  multiplier           numeric(3,1) not null default 1.0,
  created_at           timestamptz not null default now()
);

create index if not exists idx_matches_status on matches(status);
create index if not exists idx_matches_kickoff on matches(kickoff_time);


-- ─── PREDICTIONS ─────────────────────────────────────────────────────────────
create table if not exists predictions (
  id                       uuid primary key default uuid_generate_v4(),
  user_id                  uuid not null references users(id) on delete cascade,
  match_id                 uuid not null references matches(id) on delete cascade,
  predicted_team1_score    integer not null,
  predicted_team2_score    integer not null,
  points_awarded           integer,
  prediction_time          timestamptz not null default now(),
  is_locked                boolean not null default false,
  unique(user_id, match_id)
);

create index if not exists idx_predictions_user on predictions(user_id);
create index if not exists idx_predictions_match on predictions(match_id);


-- ─── WEEKLY LEADERBOARD ───────────────────────────────────────────────────────
create table if not exists weekly_leaderboard (
  id          uuid primary key default uuid_generate_v4(),
  week_number integer not null,
  user_id     uuid not null references users(id) on delete cascade,
  points      integer not null default 0,
  rank        integer not null,
  updated_at  timestamptz not null default now(),
  unique(week_number, user_id)
);

create index if not exists idx_weekly_week on weekly_leaderboard(week_number);


-- ─── OVERALL LEADERBOARD ──────────────────────────────────────────────────────
create table if not exists overall_leaderboard (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid not null references users(id) on delete cascade unique,
  points      integer not null default 0,
  rank        integer not null,
  exact_scores integer not null default 0,
  updated_at  timestamptz not null default now()
);


-- ─── ROW LEVEL SECURITY ───────────────────────────────────────────────────────
-- Service role key bypasses RLS, so our backend always has full access.
-- Enable RLS to block direct anon key access from frontend.

alter table users enable row level security;
alter table matches enable row level security;
alter table predictions enable row level security;
alter table weekly_leaderboard enable row level security;
alter table overall_leaderboard enable row level security;

-- Matches: anyone can read (public data)
create policy "matches_read_all" on matches for select using (true);

-- Leaderboards: anyone can read
create policy "overall_lb_read_all" on overall_leaderboard for select using (true);
create policy "weekly_lb_read_all" on weekly_leaderboard for select using (true);

-- All writes go through the backend (service role key), so no additional policies needed.
