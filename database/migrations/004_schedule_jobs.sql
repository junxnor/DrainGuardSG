-- 004: Scheduled jobs (Supabase only: needs pg_cron, pg_net and Vault)
--
-- Run with scripts/apply_migrations.py, which passes the two secret values as
-- transaction-local settings. The secret values never appear in this file or in git:
--   drainguard.ingest_url    -> https://drainguardsg.vercel.app/api/ingest/rainfall
--   drainguard.ingest_secret -> same value as INGEST_SECRET in Vercel
--
-- pg_cron schedules are in UTC. Singapore time (SGT) = UTC + 8.

-- 1. Turn on the scheduler and the HTTP client
--    pg_cron creates its own "cron" schema; Supabase's docs put pg_net in "extensions".
create extension if not exists pg_cron;
create extension if not exists pg_net with schema extensions;

-- 2. Store the endpoint URL and bearer secret in Supabase Vault (encrypted at rest).
--    Re-running updates the stored values instead of creating duplicates.
do $$
declare
    v_url    text := current_setting('drainguard.ingest_url', true);
    v_secret text := current_setting('drainguard.ingest_secret', true);
    v_id     uuid;
begin
    if coalesce(v_url, '') !~ '^https://' then
        raise exception 'drainguard.ingest_url must be set to an https URL';
    end if;
    if length(coalesce(v_secret, '')) < 32 then
        raise exception 'drainguard.ingest_secret must be at least 32 characters';
    end if;

    select id into v_id from vault.secrets where name = 'drainguard_ingest_url';
    if v_id is null then
        perform vault.create_secret(v_url, 'drainguard_ingest_url', 'DrainGuard rainfall ingestion endpoint');
    else
        perform vault.update_secret(v_id, v_url);
    end if;

    v_id := null;
    select id into v_id from vault.secrets where name = 'drainguard_ingest_secret';
    if v_id is null then
        perform vault.create_secret(v_secret, 'drainguard_ingest_secret', 'Bearer token for /api/ingest/rainfall');
    else
        perform vault.update_secret(v_id, v_secret);
    end if;
end;
$$;

-- 3. Rainfall ingestion every 5 minutes, at :02, :07, :12 ... so each 5-minute
--    reading has had time to publish. Scheduling the same name again replaces the job.
--    timeout_milliseconds: pg_net's default is too short for a backfill run.
select cron.schedule(
    'drainguard-rainfall-ingest',
    '2-57/5 * * * *',
    $job$
    select net.http_post(
        url := (select decrypted_secret from vault.decrypted_secrets where name = 'drainguard_ingest_url'),
        headers := jsonb_build_object(
            'Content-Type', 'application/json',
            'Authorization', 'Bearer ' || (select decrypted_secret from vault.decrypted_secrets
                                           where name = 'drainguard_ingest_secret')
        ),
        body := jsonb_build_object('trigger', 'pg_cron'),
        timeout_milliseconds := 60000
    );
    $job$
);

-- 4. Daily retention at 03:30 SGT (19:30 UTC): delete official observations older than 90 days
select cron.schedule(
    'drainguard-rainfall-retention',
    '30 19 * * *',
    $job$ select public.drainguard_purge_old_rainfall(90); $job$
);

-- 5. Weekly (Sunday 03:45 SGT): trim pg_cron's own run log, which otherwise grows forever.
--    This is scheduler housekeeping only; it does not touch any DrainGuard data.
select cron.schedule(
    'drainguard-cron-history-cleanup',
    '45 19 * * 0',
    $job$ delete from cron.job_run_details where end_time < now() - interval '14 days'; $job$
);
