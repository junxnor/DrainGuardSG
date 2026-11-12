-- 001: Official rainfall observations (data.gov.sg 5-minute totals)
--
-- This table was already created in production during stage 1 (by the backend's
-- SQLAlchemy model). This file records its exact structure so it can be recreated.
-- Every statement is "if not exists", so running it again changes nothing.

create table if not exists public.rainfall_observations (
    id            bigserial primary key,
    station_id    varchar not null,
    observed_at   timestamptz not null,          -- end of the 5-minute period
    value_mm      double precision not null,
    station_name  varchar,
    latitude      double precision,
    longitude     double precision,
    reading_type  varchar,
    source        varchar not null,                 -- always set by the backend ('data.gov.sg')
    ingested_at   timestamptz default now(),
    -- One reading per station per 5-minute period: re-running ingestion can't duplicate rows
    constraint uq_rainfall_obs_station_time unique (station_id, observed_at)
);

create index if not exists ix_rainfall_obs_observed_at
    on public.rainfall_observations (observed_at);

-- Block access through Supabase's public API keys; the backend connects as postgres.
alter table public.rainfall_observations enable row level security;
