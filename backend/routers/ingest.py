"""
Ingestion API Router
POST /api/ingest/rainfall  - run one scheduled ingestion (called by Supabase pg_cron)
GET  /api/ingest/status    - public, read-only ingestion health (no secrets)
"""

import hmac
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse

sys.path.append(str(Path(__file__).parent.parent))

from database import get_ingestion_status
from services.rainfall_ingest import run_scheduled_ingest

router = APIRouter()

SGT = timezone(timedelta(hours=8))
# Scheduler runs every 5 minutes; flag a problem if no success for 15 minutes.
HEALTHY_WITHIN = timedelta(minutes=15)
MIN_SECRET_LENGTH = 32


def _check_auth(authorization: Optional[str]) -> None:
    secret = os.getenv("INGEST_SECRET", "")
    if len(secret) < MIN_SECRET_LENGTH:
        # Fail closed: no (or weak) secret configured means nobody can trigger ingestion
        raise HTTPException(status_code=503, detail="Ingestion is not configured")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(token.encode(), secret.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Bearer"})


@router.post("/rainfall")
async def ingest_rainfall(authorization: Optional[str] = Header(default=None)):
    _check_auth(authorization)
    result = await run_scheduled_ingest()
    # 502 on failure so the failure is visible in pg_net's response log
    return JSONResponse(status_code=200 if result["ok"] else 502, content=result)


def summarize_status(status: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Public view of ingestion health. Error text is already sanitised when stored."""
    if status is None:
        return {"state": "unknown", "healthy": False, "note": "Ingestion status not available"}
    now = datetime.now(timezone.utc)
    last_success = status.get("last_success_at")
    healthy = last_success is not None and now - last_success <= HEALTHY_WITHIN
    if last_success is None:
        state = "never_succeeded"
    elif healthy:
        state = "ok"
    else:
        state = "failing" if status.get("consecutive_failures") else "stalled"

    def iso(v):
        return v.astimezone(SGT).isoformat() if isinstance(v, datetime) else None

    return {
        "state": state,
        "healthy": healthy,
        "last_attempt_at": iso(status.get("last_attempt_at")),
        "last_success_at": iso(last_success),
        "last_failure_at": iso(status.get("last_failure_at")),
        "last_error": status.get("last_error"),
        "consecutive_failures": status.get("consecutive_failures", 0),
        "total_runs": status.get("total_runs", 0),
        "total_failures": status.get("total_failures", 0),
        "last_rows_inserted": status.get("last_rows_inserted", 0),
        "latest_observed_at": iso(status.get("latest_observed_at")),
        "last_duration_ms": status.get("last_duration_ms"),
    }


@router.get("/status")
async def ingest_status():
    return summarize_status(await get_ingestion_status())
