"""
Full backup of the production public schema with pg_dump (custom format, restorable
with pg_restore). Read-only for production. The password is passed through the
PGPASSWORD environment variable of the child process and is never printed.

Usage (from repo root):  python scripts/backup_pg_dump.py
Output: backups/pgdump-<timestamp>/public.dump  (+ list of contents)
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
PG_BIN = Path(r"C:\Program Files\PostgreSQL\18\bin")


def main():
    url = (dotenv_values(ROOT / "backend" / ".env").get("DATABASE_URL") or "")
    u = urlparse(url.replace("postgresql+asyncpg://", "postgresql://", 1))
    if not u.hostname or u.hostname in ("localhost", "127.0.0.1"):
        sys.exit("backend/.env DATABASE_URL missing or points at localhost")

    out_dir = ROOT / "backups" / f"pgdump-{datetime.now():%Y%m%d-%H%M%S}"
    out_dir.mkdir(parents=True)
    dump = out_dir / "public.dump"
    env = {**os.environ, "PGPASSWORD": unquote(u.password or ""), "PGSSLMODE": "require"}
    cmd = [str(PG_BIN / "pg_dump.exe"), "-h", u.hostname, "-p", str(u.port or 5432),
           "-U", unquote(u.username or ""), "-d", (u.path or "/postgres").lstrip("/"),
           "--schema=public", "--format=custom", "--no-owner", "--no-privileges", "-f", str(dump)]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.replace(env["PGPASSWORD"], "***") if env["PGPASSWORD"] else r.stderr)
        sys.exit(f"pg_dump failed (exit {r.returncode})")

    listing = subprocess.run([str(PG_BIN / "pg_restore.exe"), "--list", str(dump)],
                             capture_output=True, text=True).stdout
    (out_dir / "contents.txt").write_text(listing, encoding="utf-8")
    tables = sorted({l.split()[-2] for l in listing.splitlines() if " TABLE DATA public " in l})
    print(f"server: {u.hostname}:{u.port}")
    print(f"dump: {dump.relative_to(ROOT)} ({dump.stat().st_size:,} bytes)")
    print(f"tables with data in dump: {tables}")


if __name__ == "__main__":
    main()
