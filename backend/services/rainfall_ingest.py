"""
Rainfall ingestion from the official data.gov.sg real-time rainfall API.

API: https://api-open.data.gov.sg/v2/real-time/api/rainfall
Each reading is the rainfall total (mm) for the 5 minutes ending at `timestamp`
(readingType "TB1 Rainfall 5 Minute Total F"). Timestamps are Singapore time (+08:00).

Optional env var DATAGOVSG_API_KEY raises the API rate limit (sent as x-api-key).
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

from database import get_all_stations, insert_rainfall_observations

logger = logging.getLogger(__name__)

API_URL = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
SGT = timezone(timedelta(hours=8))
EXPECTED_UNIT = "mm"


class RainfallApiError(Exception):
    """The API returned an error or a response we don't recognise."""


def _headers() -> Dict[str, str]:
    key = os.getenv("DATAGOVSG_API_KEY")
    return {"x-api-key": key} if key else {}


def parse_rainfall_response(
    payload: Dict[str, Any], station_filter: Optional[Set[str]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, int], Optional[str]]:
    """
    Validate one API page and convert it to rainfall_observations rows.
    Returns (rows, counts of skipped values by reason, pagination token).
    Raises RainfallApiError if the page itself is not a valid rainfall response.
    """
    if not isinstance(payload, dict) or payload.get("code") != 0:
        raise RainfallApiError(f"API error: code={payload.get('code')} msg={payload.get('errorMsg')}")
    data = payload.get("data") or {}
    unit = data.get("readingUnit")
    reading_type = data.get("readingType") or ""
    if unit != EXPECTED_UNIT:
        raise RainfallApiError(f"Unexpected readingUnit {unit!r}, expected 'mm'")
    if "5 Minute" not in reading_type:
        raise RainfallApiError(f"Unexpected readingType {reading_type!r}, expected 5-minute totals")

    stations = {s.get("id"): s for s in data.get("stations") or [] if s.get("id")}
    skipped = {"filtered": 0, "bad_value": 0, "bad_timestamp": 0, "unknown_station": 0}
    rows: List[Dict[str, Any]] = []

    for block in data.get("readings") or []:
        try:
            observed_at = datetime.fromisoformat(block["timestamp"])
            if observed_at.tzinfo is None:
                raise ValueError("timestamp has no timezone")
        except (KeyError, TypeError, ValueError):
            skipped["bad_timestamp"] += len(block.get("data") or [])
            continue
        for item in block.get("data") or []:
            sid = item.get("stationId")
            if station_filter is not None and sid not in station_filter:
                skipped["filtered"] += 1
                continue
            value = item.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not (0 <= value <= 300):
                skipped["bad_value"] += 1
                continue
            meta = stations.get(sid)
            if meta is None:
                skipped["unknown_station"] += 1
                continue
            loc = meta.get("location") or {}
            rows.append({
                "station_id": sid,
                "observed_at": observed_at,
                "value_mm": float(value),
                "station_name": meta.get("name"),
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "reading_type": reading_type,
                "source": "data.gov.sg",
            })
    return rows, skipped, data.get("paginationToken")


# data.gov.sg allows 6 real-time calls per 10 s without a key. The limit resets every
# 10 s. Docs say HTTP 429; in practice the body can also carry code 24.
RATE_LIMIT_CODE = 24
RATE_LIMIT_WAIT_S = 10
PAGE_DELAY_S = 2.0


async def _get(client: httpx.AsyncClient, params: Dict[str, str], retries: int = 2) -> Dict[str, Any]:
    """GET one page. Waits and retries on rate limiting or a server error."""
    for attempt in range(retries + 1):
        resp = await client.get(API_URL, params=params, headers=_headers(), timeout=20)
        body: Dict[str, Any] = {}
        try:
            body = resp.json()
        except ValueError:
            pass
        limited = resp.status_code == 429 or body.get("code") == RATE_LIMIT_CODE
        if (limited or resp.status_code >= 500) and attempt < retries:
            await asyncio.sleep(RATE_LIMIT_WAIT_S)
            continue
        if limited:
            raise RainfallApiError("data.gov.sg rate limit exceeded")
        if resp.status_code != 200:
            raise RainfallApiError(f"HTTP {resp.status_code} from data.gov.sg")
        return body
    raise RainfallApiError("data.gov.sg did not respond after retries")


async def _tracked_station_ids() -> Set[str]:
    """Stations shown on the dashboard. Only these are stored, to keep the table small."""
    return {s["station_id"] for s in await get_all_stations()}


async def ingest_latest() -> Dict[str, Any]:
    """Fetch the most recent 5-minute block and store it. Safe to run repeatedly."""
    station_ids = await _tracked_station_ids()
    async with httpx.AsyncClient() as client:
        payload = await _get(client, {})
    rows, skipped, _ = parse_rainfall_response(payload, station_ids)
    inserted = await insert_rainfall_observations(rows)
    latest = max((r["observed_at"] for r in rows), default=None)
    result = {
        "mode": "latest",
        "fetched": len(rows),
        "inserted": inserted,
        "skipped": skipped,
        "latest_observed_at": latest.astimezone(SGT).isoformat() if latest else None,
    }
    logger.info(f"Rainfall ingest: {result}")
    return result


async def fetch_history_since(
    client: httpx.AsyncClient, cutoff: datetime, station_ids: Set[str], max_pages: int
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Readings with observed_at > cutoff from the API's per-day history.
    Verified behaviour: each SGT day is paginated newest first, 25 five-minute blocks
    per page, no overlap between pages. Walks today first, then earlier days, and stops
    once a page reaches the cutoff. Returns (rows, pages fetched).
    """
    now_sgt = datetime.now(SGT)
    day = now_sgt.date()
    rows_out: List[Dict[str, Any]] = []
    pages = 0
    while day >= cutoff.astimezone(SGT).date() and pages < max_pages:
        token: Optional[str] = None
        reached_cutoff = False
        while pages < max_pages:
            params = {"date": day.isoformat()}
            if token:
                params["paginationToken"] = token
            if pages:
                await asyncio.sleep(PAGE_DELAY_S)
            payload = await _get(client, params)
            pages += 1
            rows, _, token = parse_rainfall_response(payload, station_ids)
            rows_out.extend(r for r in rows if r["observed_at"] > cutoff)
            oldest = min((r["observed_at"] for r in rows), default=None)
            if oldest is not None and oldest <= cutoff:
                reached_cutoff = True
            if not token or reached_cutoff:
                break
        if reached_cutoff:
            break
        day -= timedelta(days=1)
    return rows_out, pages


async def ingest_recent(hours: float = 3, max_pages: int = 40) -> Dict[str, Any]:
    """Manual backfill of the last `hours` (used by scripts/ingest_rainfall.py)."""
    station_ids = await _tracked_station_ids()
    cutoff = datetime.now(SGT) - timedelta(hours=hours)
    async with httpx.AsyncClient() as client:
        all_rows, pages = await fetch_history_since(client, cutoff, station_ids, max_pages)
    inserted = await insert_rainfall_observations(all_rows)
    result = {
        "mode": "recent",
        "hours": hours,
        "pages": pages,
        "fetched": len(all_rows),
        "inserted": inserted,
        "oldest": min((r["observed_at"] for r in all_rows), default=cutoff).astimezone(SGT).isoformat(),
        "newest": max((r["observed_at"] for r in all_rows), default=cutoff).astimezone(SGT).isoformat(),
    }
    logger.info(f"Rainfall backfill: {result}")
    return result


# ---------------------------------------------------------------------------
# Scheduled run (called by POST /api/ingest/rainfall every 5 minutes)
# ---------------------------------------------------------------------------

BLOCK = timedelta(minutes=5)
MAX_BACKFILL = timedelta(hours=3)   # the risk calculation only needs the last 3 hours
MAX_BACKFILL_PAGES = 6              # 3 h is 2 pages, plus room for crossing midnight
RUN_TIMEOUT_S = 45                  # well inside Vercel's function limit and pg_net's 60 s


async def _scheduled_ingest_body() -> Dict[str, Any]:
    from database import get_latest_observation_time  # local import avoids a cycle at startup

    station_ids = await _tracked_station_ids()
    stored_latest = await get_latest_observation_time()

    async with httpx.AsyncClient() as client:
        payload = await _get(client, {})
        latest_rows, skipped, _ = parse_rainfall_response(payload, station_ids)
        api_latest = max((r["observed_at"] for r in latest_rows), default=None)
        if api_latest is None:
            raise RainfallApiError("API returned no readings for the tracked stations")

        result: Dict[str, Any] = {
            "api_latest": api_latest,
            "stored_latest_before": stored_latest,
            "pages": 1,
            "backfilled": False,
        }

        if stored_latest is not None and api_latest <= stored_latest:
            # Nothing new since the last run: skip the insert entirely
            result.update(fetched=len(latest_rows), inserted=0, action="up_to_date")
            return result

        if stored_latest is None or api_latest - stored_latest > BLOCK:
            # Missed one or more 5-minute blocks: fill the gap (at most the last 3 hours)
            cutoff = max(stored_latest or api_latest - MAX_BACKFILL, api_latest - MAX_BACKFILL)
            history, pages = await fetch_history_since(client, cutoff, station_ids, MAX_BACKFILL_PAGES)
            rows = {(r["station_id"], r["observed_at"]): r for r in history + latest_rows}
            to_insert = list(rows.values())
            result.update(pages=1 + pages, backfilled=True, backfill_from=cutoff)
        else:
            to_insert = latest_rows

    inserted = await insert_rainfall_observations(to_insert)
    result.update(fetched=len(to_insert), inserted=inserted, action="inserted" if inserted else "no_new_rows")
    return result


def _safe_error(e: BaseException) -> str:
    """Short error text for the status table. Never includes connection strings or SQL."""
    if isinstance(e, RainfallApiError):
        msg = str(e)
        return (msg if msg.startswith("data.gov.sg") else f"data.gov.sg: {msg}")[:300]
    if isinstance(e, asyncio.TimeoutError):
        return f"Run exceeded {RUN_TIMEOUT_S}s"
    if isinstance(e, httpx.HTTPError):
        return f"Network error calling data.gov.sg ({type(e).__name__})"
    return f"Internal error ({type(e).__name__})"


async def run_scheduled_ingest() -> Dict[str, Any]:
    """
    One scheduled ingestion run. Always records the outcome in ingestion_status.
    Returns {"ok": bool, ...}; never raises.
    """
    from database import record_ingestion_result

    started = datetime.now(timezone.utc)
    try:
        result = await asyncio.wait_for(_scheduled_ingest_body(), timeout=RUN_TIMEOUT_S)
        ok, error = True, None
    except Exception as e:  # noqa: BLE001 - every failure must be recorded
        logger.exception("Scheduled rainfall ingest failed")
        result, ok, error = {}, False, _safe_error(e)

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    status = await record_ingestion_result(
        ok=ok,
        error=error,
        rows_inserted=result.get("inserted", 0),
        latest_observed_at=result.get("api_latest"),
        duration_ms=duration_ms,
    )

    def iso(v):
        return v.astimezone(SGT).isoformat() if isinstance(v, datetime) else v

    out = {k: iso(v) for k, v in result.items()}
    out.update(ok=ok, error=error, duration_ms=duration_ms, status_recorded=status is not None)
    logger.info(f"Scheduled ingest: {out}")
    return out
