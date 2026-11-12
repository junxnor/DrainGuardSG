"""
Fetch official rainfall from data.gov.sg and store it in Supabase (rainfall_observations).

Usage (from repo root):
  python scripts/ingest_rainfall.py            # latest 5-minute block
  python scripts/ingest_rainfall.py --hours 3  # backfill the last 3 hours

Creates the rainfall_observations table if it does not exist.
Existing tables and rows are never modified or deleted.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import ensure_observations_table  # noqa: E402
from services.rainfall_ingest import ingest_latest, ingest_recent  # noqa: E402


async def main(hours: float | None):
    await ensure_observations_table()
    result = await (ingest_recent(hours) if hours else ingest_latest())
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=None, help="Backfill this many hours")
    asyncio.run(main(parser.parse_args().hours))
