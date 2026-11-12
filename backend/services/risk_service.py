"""
Risk Assessment Service
Rule-based risk estimation from official data.gov.sg rainfall observations.

This is a transparent threshold formula, not a trained or AI model, and not a
flood forecast. Thresholds are heuristics and have not been calibrated against
recorded flood events.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database import get_all_stations, get_rainfall_observations_since, get_latest_observation_time

SGT = timezone(timedelta(hours=8))

# Data older than this is treated as unavailable rather than "no rain".
STALE_AFTER = timedelta(minutes=30)
# A station must have a reading this close to the newest reading to count as current.
STATION_GAP = timedelta(minutes=10)

# Score weights (sum to 1.0). Each component is scaled to 0-100 first.
WEIGHTS = {"intensity": 0.40, "accum_15min": 0.15, "accum_1hr": 0.25, "accum_3hr": 0.20}
# Rainfall that maps to a full component score of 100.
FULL_SCALE = {"intensity_mm_hr": 50.0, "accum_15min": 10.0, "accum_1hr": 30.0, "accum_3hr": 50.0}


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    NO_DATA = "no_data"


def classify_risk_level(risk_score: float) -> RiskLevel:
    """Classify risk level based on score (0-100)"""
    if risk_score >= 76:
        return RiskLevel.CRITICAL
    elif risk_score >= 51:
        return RiskLevel.HIGH
    elif risk_score >= 26:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW


def calculate_risk_score(
    current_rainfall: float,
    rainfall_15min: float = 0,
    rainfall_1hr: float = 0,
    rainfall_3hr: float = 0,
) -> float:
    """
    Risk score 0-100 from rainfall amounts (mm).

    current_rainfall: latest 5-minute total, converted to an hourly rate.
    Each component is capped at 100, then combined with WEIGHTS, so heavy rain
    on every measure gives 100 and no rain gives 0.
    """
    intensity_mm_hr = current_rainfall * 12
    components = {
        "intensity": min(intensity_mm_hr / FULL_SCALE["intensity_mm_hr"] * 100, 100),
        "accum_15min": min(rainfall_15min / FULL_SCALE["accum_15min"] * 100, 100),
        "accum_1hr": min(rainfall_1hr / FULL_SCALE["accum_1hr"] * 100, 100),
        "accum_3hr": min(rainfall_3hr / FULL_SCALE["accum_3hr"] * 100, 100),
    }
    return min(sum(components[k] * w for k, w in WEIGHTS.items()), 100)


def _sgt_iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.astimezone(SGT).isoformat() if dt else None


async def calculate_station_risks() -> List[Dict[str, Any]]:
    """
    Risk for each dashboard station, using official 5-minute rainfall totals
    stored in rainfall_observations. All windows end at the newest stored reading.
    Stations without current data get risk_level "no_data", never "low".
    """
    stations = await get_all_stations()
    now = datetime.now(timezone.utc)
    reference = await get_latest_observation_time()

    fresh = reference is not None and (now - reference) <= STALE_AFTER
    observations: List[Dict[str, Any]] = []
    if fresh:
        observations = await get_rainfall_observations_since(
            reference - timedelta(hours=3), [s["station_id"] for s in stations]
        )

    by_station: Dict[str, List[Dict[str, Any]]] = {}
    for o in observations:
        by_station.setdefault(o["station_id"], []).append(o)

    if reference is None:
        reason = "No official rainfall readings stored yet"
    elif not fresh:
        minutes = int((now - reference).total_seconds() // 60)
        reason = f"Newest official reading is {minutes} minutes old"
    else:
        reason = None

    results = []
    for station in stations:
        obs = by_station.get(station["station_id"], [])
        latest = obs[-1] if obs else None
        base = {
            "station_id": station["station_id"],
            "station_name": (latest or {}).get("station_name") or station["station_name"],
            "longitude": station["longitude"],
            "latitude": station["latitude"],
            "source": "data.gov.sg",
        }

        if not fresh or latest is None or (reference - latest["observed_at"]) > STATION_GAP:
            results.append({
                **base,
                "risk_level": RiskLevel.NO_DATA.value,
                "risk_score": 0.0,
                "current_rainfall": 0.0,
                "rainfall_15min": 0.0,
                "rainfall_1hr": 0.0,
                "rainfall_3hr": 0.0,
                "readings_3hr": len(obs),
                "data_status": "no_data",
                "data_note": reason or "No current reading from this station",
                "observed_at": _sgt_iso(latest["observed_at"]) if latest else None,
                "last_updated": _sgt_iso(latest["observed_at"]) if latest else None,
            })
            continue

        def total(window: timedelta) -> float:
            return round(sum(o["value_mm"] for o in obs if o["observed_at"] > reference - window), 1)

        current = round(latest["value_mm"], 1)
        r15, r1h, r3h = total(timedelta(minutes=15)), total(timedelta(hours=1)), total(timedelta(hours=3))
        score = calculate_risk_score(current, r15, r1h, r3h)
        results.append({
            **base,
            "risk_level": classify_risk_level(score).value,
            "risk_score": round(score, 2),
            "current_rainfall": current,
            "rainfall_15min": r15,
            "rainfall_1hr": r1h,
            "rainfall_3hr": r3h,
            "readings_3hr": len(obs),
            "data_status": "ok",
            "data_note": None,
            "observed_at": _sgt_iso(latest["observed_at"]),
            "last_updated": _sgt_iso(latest["observed_at"]),
        })
    return results


async def calculate_risk_overview() -> Dict[str, Any]:
    """Overall risk summary across stations that have current data."""
    station_risks = await calculate_station_risks()

    risk_counts = {level.value: 0 for level in RiskLevel}
    for risk in station_risks:
        risk_counts[risk["risk_level"]] += 1

    with_data = [r for r in station_risks if r["data_status"] == "ok"]
    high_risk_stations = [
        r["station_id"] for r in with_data
        if r["risk_level"] in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value)
    ]

    if with_data:
        avg_score = sum(r["risk_score"] for r in with_data) / len(with_data)
        overall_risk = classify_risk_level(avg_score)
        # A critical station raises the overall level even if the average is lower
        if risk_counts[RiskLevel.CRITICAL.value] > 0 and overall_risk in (RiskLevel.LOW, RiskLevel.MODERATE):
            overall_risk = RiskLevel.HIGH
        data_status = "ok"
    else:
        avg_score = 0.0
        overall_risk = RiskLevel.NO_DATA
        data_status = "no_data"

    observed = [r["observed_at"] for r in with_data if r["observed_at"]]
    return {
        "overall_risk": overall_risk.value,
        "risk_score": round(avg_score, 2),
        "high_risk_count": risk_counts[RiskLevel.HIGH.value],
        "moderate_risk_count": risk_counts[RiskLevel.MODERATE.value],
        "low_risk_count": risk_counts[RiskLevel.LOW.value],
        "critical_count": risk_counts[RiskLevel.CRITICAL.value],
        "no_data_count": risk_counts[RiskLevel.NO_DATA.value],
        "total_stations": len(station_risks),
        "stations_with_data": len(with_data),
        "data_status": data_status,
        "data_note": None if with_data else (station_risks[0]["data_note"] if station_risks else "No stations configured"),
        "source": "data.gov.sg",
        "last_updated": max(observed) if observed else None,
        "high_risk_stations": high_risk_stations,
    }
