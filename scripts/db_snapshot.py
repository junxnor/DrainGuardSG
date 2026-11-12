"""
Read-only snapshot of the production database, for before/after comparisons.

Usage (from repo root):
  python scripts/db_snapshot.py before.json
  python scripts/db_snapshot.py after.json --compare before.json

Records, for every table in the public schema: row count and an MD5 checksum of all
rows (so any changed, added or deleted row shows up). Also records installed
extensions, DrainGuard functions, DrainGuard Vault entries (names only, never values)
and pg_cron jobs. Runs inside a READ ONLY transaction.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

import asyncpg
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = dotenv_values(ROOT / "backend" / ".env")


async def snapshot() -> dict:
    url = (ENV_FILE.get("DATABASE_URL") or "").replace("postgresql+asyncpg://", "postgresql://", 1)
    if not url or "localhost" in url:
        sys.exit("backend/.env DATABASE_URL missing or points at localhost")
    c = await asyncpg.connect(url, statement_cache_size=0)
    try:
        async with c.transaction(readonly=True):
            # Fixed settings so checksums don't depend on the server's display options
            await c.execute("set local timezone = 'UTC'; set local datestyle = 'ISO, MDY'; "
                            "set local extra_float_digits = 1")
            snap = {"server": url.split("@")[-1].split("/")[0]}
            tables = [r[0] for r in await c.fetch(
                "select tablename from pg_tables where schemaname='public' order by 1")]
            snap["tables"] = {}
            for t in tables:
                n = await c.fetchval(f'select count(*) from public."{t}"')
                md5 = await c.fetchval(
                    f'select md5(coalesce(string_agg(x::text, \'|\' order by x::text), \'\')) from public."{t}" x')
                snap["tables"][t] = {"rows": n, "md5": md5}
            snap["extensions"] = {r[0]: r[1] for r in await c.fetch(
                "select extname, extversion from pg_extension order by 1")}
            snap["schemas"] = [r[0] for r in await c.fetch(
                "select nspname from pg_namespace where nspname in ('cron','net','vault','extensions') order by 1")]
            snap["drainguard_functions"] = [r[0] for r in await c.fetch(
                "select p.proname from pg_proc p join pg_namespace n on n.oid=p.pronamespace "
                "where n.nspname='public' and p.proname like 'drainguard%' order by 1")]
            snap["vault_drainguard_names"] = [r[0] for r in await c.fetch(
                "select name from vault.secrets where name like 'drainguard%' order by 1")]
            snap["vault_total_secrets"] = await c.fetchval("select count(*) from vault.secrets")
            snap["cron_jobs"] = (
                [dict(r) for r in await c.fetch("select jobname, schedule, active from cron.job order by jobname")]
                if await c.fetchval("select to_regclass('cron.job') is not null") else None)
    finally:
        await c.close()
    return snap


def compare(before: dict, after: dict) -> bool:
    same = True
    keys = sorted(set(before) | set(after))
    for k in keys:
        if k == "tables":
            for t in sorted(set(before["tables"]) | set(after["tables"])):
                b, a = before["tables"].get(t), after["tables"].get(t)
                ok = b == a
                same &= ok
                print(f"  {'same' if ok else 'CHANGED'}  table {t:<28} rows {b and b['rows']} -> {a and a['rows']}")
        else:
            ok = before.get(k) == after.get(k)
            same &= ok
            print(f"  {'same' if ok else 'CHANGED'}  {k}: {after.get(k) if ok else (before.get(k), after.get(k))}")
    return same


async def main(args):
    snap = await snapshot()
    Path(args.out).write_text(json.dumps(snap, indent=1, default=str), encoding="utf-8")
    print(f"snapshot of {snap['server']} written to {args.out}")
    if args.compare:
        before = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        identical = compare(before, json.loads(json.dumps(snap, default=str)))
        print("RESULT: production identical to before" if identical else "RESULT: PRODUCTION CHANGED")
        sys.exit(0 if identical else 1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("out")
    p.add_argument("--compare")
    asyncio.run(main(p.parse_args()))
