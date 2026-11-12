"""
Apply DrainGuard SQL migrations from database/migrations/.

Usage (from repo root):
  python scripts/apply_migrations.py --target test  001 002 003          # local test DB
  python scripts/apply_migrations.py --target prod --dry-run 001 002 003 004
  python scripts/apply_migrations.py --target prod 001 002 003 004

  --dry-run  runs every file inside one transaction and then ROLLS BACK, so the
             SQL is checked against the real database but nothing is kept.

Each run is a single transaction: if any statement fails, nothing is applied.
Migration 004 needs INGEST_SECRET (from backend/.env) and INGEST_URL (defaults to the
production endpoint). They are passed as transaction-local settings, never written to disk.
"""
import argparse
import asyncio
import sys
from pathlib import Path

import asyncpg
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "database" / "migrations"
# Read production settings only from backend/.env. Shell environment variables are
# ignored on purpose, so a leftover DATABASE_URL can never redirect a run.
ENV_FILE = dotenv_values(ROOT / "backend" / ".env")

TEST_URL = "postgresql://postgres@localhost:55432/drainguard_test"
DEFAULT_INGEST_URL = "https://drainguardsg.vercel.app/api/ingest/rainfall"


def resolve(prefixes):
    files = []
    for p in prefixes:
        match = sorted(MIGRATIONS.glob(f"{p}*.sql"))
        if len(match) != 1:
            sys.exit(f"Expected exactly one migration starting with {p!r}, found {len(match)}")
        files.append(match[0])
    return files


async def verify_inside_transaction(conn, files):
    """Check what the migrations created, before commit/rollback. Never prints secret values."""
    names = {f.name[:3] for f in files}
    if "002" in names:
        print(f"  check ingestion_status rows: {await conn.fetchval('select count(*) from public.ingestion_status')}")
    if "003" in names:
        ok = await conn.fetchval("select to_regprocedure('public.drainguard_purge_old_rainfall(integer,integer)') is not null")
        print(f"  check purge function exists: {ok}")
        try:
            await conn.execute("savepoint guard")
            await conn.fetchval("select public.drainguard_purge_old_rainfall(30)")
            print("  check keep_days=30 refused: NO (unexpected)")
        except asyncpg.PostgresError:
            print("  check keep_days=30 refused: yes")
        finally:
            await conn.execute("rollback to savepoint guard")
        would_delete = await conn.fetchval(
            "select count(*) from public.rainfall_observations where observed_at < now() - interval '90 days'")
        print(f"  check rows a purge would delete today: {would_delete}")
    if "004" in names:
        exts = [r[0] for r in await conn.fetch(
            "select extname from pg_extension where extname in ('pg_cron','pg_net') order by 1")]
        print(f"  check extensions enabled: {exts}")
        for r in await conn.fetch("select jobname, schedule, active from cron.job "
                                  "where jobname like 'drainguard-%' order by jobname"):
            print(f"  check cron job: {r['jobname']:<34} schedule='{r['schedule']}' active={r['active']}")
        url = await conn.fetchval("select decrypted_secret from vault.decrypted_secrets where name='drainguard_ingest_url'")
        secret_ok = await conn.fetchval(
            "select decrypted_secret = $1 from vault.decrypted_secrets where name='drainguard_ingest_secret'",
            ENV_FILE.get("INGEST_SECRET") or "")
        print(f"  check vault url: {url}")
        print(f"  check vault secret matches backend/.env INGEST_SECRET: {secret_ok} (value not shown)")


async def main(args):
    if args.target == "prod":
        url = (ENV_FILE.get("DATABASE_URL") or "").replace("postgresql+asyncpg://", "postgresql://", 1)
        if not url:
            sys.exit("DATABASE_URL missing in backend/.env")
        if "localhost" in url or "127.0.0.1" in url:
            sys.exit("backend/.env DATABASE_URL points at localhost; refusing --target prod")
    else:
        url = TEST_URL
    files = resolve(args.migrations)

    conn = await asyncpg.connect(url, statement_cache_size=0)
    host = await conn.fetchval("select coalesce(inet_server_addr()::text, 'local socket')")
    has_vault = await conn.fetchval("select to_regnamespace('vault') is not null")
    print(f"Connected to {args.target}: server {host}, Supabase Vault present: {has_vault}")
    if args.target == "prod" and not has_vault:
        await conn.close()
        sys.exit("Target has no Supabase Vault schema; this is not the Supabase database. Stopping.")
    tx = conn.transaction()
    await tx.start()
    try:
        if any(f.name.startswith("004") for f in files):
            secret = ENV_FILE.get("INGEST_SECRET") or ""
            await conn.execute("select set_config('drainguard.ingest_url', $1, true)",
                               ENV_FILE.get("INGEST_URL") or DEFAULT_INGEST_URL)
            await conn.execute("select set_config('drainguard.ingest_secret', $1, true)", secret)
        for f in files:
            await conn.execute(f.read_text(encoding="utf-8"))
            print(f"ok   {f.name}")
        await verify_inside_transaction(conn, files)
        if args.dry_run:
            await tx.rollback()
            print("DRY RUN: all statements succeeded, transaction rolled back, nothing kept")
        else:
            await tx.commit()
            print(f"Committed {len(files)} migration(s) to {args.target}")
    except Exception as e:
        await tx.rollback()
        print(f"FAILED, rolled back, nothing applied: {type(e).__name__}: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["test", "prod"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("migrations", nargs="+", help="Migration number prefixes, e.g. 001 002")
    asyncio.run(main(parser.parse_args()))
