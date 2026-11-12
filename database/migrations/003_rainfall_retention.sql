-- 003: 90-day retention for official rainfall observations
--
-- Creates a function only. It deletes nothing until it is called (by the daily
-- job in migration 004).
--
-- Safety rules built into the function:
--   * Only touches public.rainfall_observations. The legacy tables
--     (rainfall_readings, stations, sensors, pub_water_level_sensors,
--     flood_prone_area_statistics) are never touched.
--   * Refuses to keep fewer than 90 days.
--   * Deletes in batches so a large cleanup can't lock the table for long.
--   * Returns the number of rows deleted.

create or replace function public.drainguard_purge_old_rainfall(
    keep_days  integer default 90,
    batch_size integer default 5000
)
returns bigint
language plpgsql
set search_path = public, pg_temp
as $$
declare
    cutoff  timestamptz;
    deleted bigint := 0;
    n       integer;
begin
    if keep_days is null or keep_days < 90 then
        raise exception 'keep_days must be at least 90 (got %)', keep_days;
    end if;
    if batch_size is null or batch_size < 1 or batch_size > 50000 then
        raise exception 'batch_size must be between 1 and 50000 (got %)', batch_size;
    end if;

    cutoff := now() - make_interval(days => keep_days);

    loop
        delete from public.rainfall_observations
        where id in (
            select id from public.rainfall_observations
            where observed_at < cutoff
            order by observed_at
            limit batch_size
        );
        get diagnostics n = row_count;
        deleted := deleted + n;
        exit when n < batch_size;
    end loop;

    return deleted;
end;
$$;

-- Supabase exposes public functions over its API. Only the database owner may run this.
revoke all on function public.drainguard_purge_old_rainfall(integer, integer) from public;
do $$
begin
    if exists (select 1 from pg_roles where rolname = 'anon') then
        revoke all on function public.drainguard_purge_old_rainfall(integer, integer) from anon;
    end if;
    if exists (select 1 from pg_roles where rolname = 'authenticated') then
        revoke all on function public.drainguard_purge_old_rainfall(integer, integer) from authenticated;
    end if;
end;
$$;
