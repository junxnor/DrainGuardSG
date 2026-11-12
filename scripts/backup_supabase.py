"""
Read-only backup of DrainGuard tables in Supabase to local JSON files.
Also prints each table's columns and row count.

Usage (from repo root):  python scripts/backup_supabase.py
Output: backups/supabase-<timestamp>/<table>.json
"""
import asyncio
import json
import sys
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

import asyncpg
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
# Read only from backend/.env so a leftover shell variable can't change the target
ENV_FILE = dotenv_values(ROOT / "backend" / ".env")

TABLES = ["rainfall_readings", "stations", "sensors", "pub_water_level_sensors",
          "rainfall_observations", "flood_prone_area_statistics", "ingestion_status"]


def _plain(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


async def main():
    url = (ENV_FILE.get("DATABASE_URL") or "").replace("postgresql+asyncpg://", "postgresql://", 1)
    if not url:
        sys.exit("DATABASE_URL not set in backend/.env")
    out = ROOT / "backups" / f"supabase-{datetime.now():%Y%m%d-%H%M%S}"
    out.mkdir(parents=True, exist_ok=True)

    conn = await asyncpg.connect(url, statement_cache_size=0)
    try:
        for table in TABLES:
            cols = await conn.fetch(
                "SELECT column_name, data_type, column_default, is_nullable "
                "FROM information_schema.columns WHERE table_schema='public' AND table_name=$1 "
                "ORDER BY ordinal_position", table)
            if not cols:
                print(f"{table}: not found")
                continue
            rows = await conn.fetch(f'SELECT * FROM public."{table}"')
            data = [{k: _plain(v) for k, v in dict(r).items()} for r in rows]
            (out / f"{table}.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
            print(f"{table}: {len(rows)} rows")
            for c in cols:
                print(f"   {c['column_name']:<16} {c['data_type']:<28} null={c['is_nullable']} default={c['column_default']}")
    finally:
        await conn.close()
    print(f"Backup written to {out}")


if __name__ == "__main__":
    asyncio.run(main())
