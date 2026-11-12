-- 002: Ingestion status (one row) for monitoring the scheduled rainfall collection
--
-- Each ingestion run updates this single row, so monitoring costs one small write
-- per run. Nothing existing is changed.

create table if not exists public.ingestion_status (
    id                    smallint primary key default 1,
    last_attempt_at       timestamptz,
    last_success_at       timestamptz,
    last_failure_at       timestamptz,
    last_error            text,
    consecutive_failures  integer not null default 0,
    total_runs            bigint  not null default 0,
    total_failures        bigint  not null default 0,
    last_rows_inserted    integer not null default 0,
    latest_observed_at    timestamptz,                 -- newest official reading stored
    last_duration_ms      integer,
    updated_at            timestamptz not null default now(),
    constraint ingestion_status_single_row check (id = 1)
);

insert into public.ingestion_status (id) values (1)
on conflict (id) do nothing;

alter table public.ingestion_status enable row level security;
