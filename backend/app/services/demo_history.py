"""Load the local Public InfoBanjir demonstration history and model."""
from __future__ import annotations

import csv
from pathlib import Path

import joblib
import pandas as pd

from ..config import DATA

CSV_DIR = DATA / "processed" / "user_provided_csv"
MODEL_PATH = DATA / "processed" / "drainguard_demo_rainfall_model.joblib"
HISTORY_DATES = [f"2026-11-{day:02d}" for day in range(7, 12)]
HISTORY_COLUMNS = [f"daily_2026_11_{day:02d}_mm" for day in range(7, 12)]
DISTRICTS_BY_STATE = {
    "Selangor": ["Gombak", "Hulu Langat", "Hulu Selangor", "Klang", "Kuala Langat", "Kuala Selangor", "Petaling", "Sabak Bernam", "Sepang"],
    "Kuala Lumpur": ["Bentong (WPKL)", "Gombak (WPKL)", "Hulu Langat (WPKL)", "Kuala Lumpur", "Wilayah Persekutuan"],
    "Putrajaya": ["Putrajaya"],
}


def canonical_district(state, value):
    """Map OCR variants onto the state-specific district labels used by PIB."""
    raw = " ".join(str(value or "").lower().replace("(wpkl)", " ").split())
    if state == "Putrajaya":
        return "Putrajaya"
    if state == "Kuala Lumpur":
        if "bentong" in raw: return "Bentong (WPKL)"
        if "gombak" in raw: return "Gombak (WPKL)"
        if "hulu langat" in raw: return "Hulu Langat (WPKL)"
        if "kuala" in raw or "lumpur" in raw: return "Kuala Lumpur"
        return "Wilayah Persekutuan"
    if state == "Selangor":
        if "gombak" in raw: return "Gombak"
        if "hulu selangor" in raw or raw == "selangor": return "Hulu Selangor"
        if "kuala selangor" in raw: return "Kuala Selangor"
        if "kuala langat" in raw: return "Kuala Langat"
        if "hulu langat" in raw or "langat" in raw: return "Hulu Langat"
        if "petaling" in raw: return "Petaling"
        if "sabak" in raw: return "Sabak Bernam"
        if "sepang" in raw: return "Sepang"
        if "klang" in raw: return "Klang"
        return "Kuala Selangor" if "selangor" in raw else "Hulu Langat"
    return str(value or "")


def number(value):
    try:
        result = float(value)
        return None if result <= -9999 else result
    except (TypeError, ValueError):
        return None


def _read_csv(name):
    with (CSV_DIR / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_demo_history():
    rainfall = []
    model_bundle = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
    model = model_bundle["model"] if model_bundle else None
    for raw in _read_csv("rainfall_all_states.csv"):
        history = [number(raw.get(column)) for column in HISTORY_COLUMNS]
        forecast = None
        if model and all(value is not None for value in history):
            forecast = max(0.0, float(model.predict(pd.DataFrame([history], columns=model_bundle["features"]))[0]))
        rainfall.append({
            "state": raw.get("state", ""), "district": canonical_district(raw.get("state"), raw.get("district")),
            "station_id": raw.get("station_id", ""), "station_name": raw.get("station_name", ""),
            "last_updated": raw.get("last_updated", ""), "history_dates": HISTORY_DATES,
            "daily_history_mm": history, "rainfall_from_midnight_mm": number(raw.get("rainfall_from_midnight_mm")),
            "rainfall_1h_mm": number(raw.get("total_1_hour_mm")),
            "predicted_next_day_mm": round(forecast, 1) if forecast is not None else None,
            "source_document": raw.get("source_document", ""), "source_page": raw.get("source_page", ""),
        })
    water = []
    for raw in _read_csv("waterlevel_all_states.csv"):
        water.append({
            "state": raw.get("state", ""), "district": canonical_district(raw.get("state"), raw.get("district")),
            "station_id": raw.get("station_id", ""), "station_name": raw.get("station_name", ""),
            "main_basin": raw.get("main_basin", ""), "sub_river_basin": raw.get("sub_river_basin", ""),
            "last_updated": raw.get("last_updated", ""), "water_level_m": number(raw.get("water_level_m")),
            "normal_m": number(raw.get("threshold_normal_m")), "alert_m": number(raw.get("threshold_alert_m")),
            "warning_m": number(raw.get("threshold_warning_m")), "danger_m": number(raw.get("threshold_danger_m")),
            "source_document": raw.get("source_document", ""), "source_page": raw.get("source_page", ""),
        })
    metadata = model_bundle.get("metrics", {}) if model_bundle else {}
    return rainfall, water, metadata


def flood_outlook(rainfall, water):
    forecasts = [row["predicted_next_day_mm"] for row in rainfall if row.get("predicted_next_day_mm") is not None]
    max_rain = max(forecasts, default=None)
    avg_rain = sum(forecasts) / len(forecasts) if forecasts else None
    ratios = [r["water_level_m"] / r["danger_m"] for r in water
              if r.get("water_level_m") is not None and r.get("danger_m") not in (None, 0)]
    max_ratio = max(ratios, default=None)
    stage_priority = {"normal": 0, "alert": 1, "warning": 2, "danger": 3}
    stage_status = "normal"
    for row in water:
        level = row.get("water_level_m")
        if level is None:
            continue
        status = "danger" if row.get("danger_m") is not None and level >= row["danger_m"] else \
                 "warning" if row.get("warning_m") is not None and level >= row["warning_m"] else \
                 "alert" if row.get("alert_m") is not None and level >= row["alert_m"] else "normal"
        if stage_priority[status] > stage_priority[stage_status]:
            stage_status = status
    max_level_row = max((r for r in water if r.get("water_level_m") is not None), key=lambda r: r["water_level_m"], default=None)
    max_stage = max_level_row["water_level_m"] if max_level_row else None
    max_danger = max_level_row.get("danger_m") if max_level_row else None

    # Transparent demo score combines a short-history rainfall estimate with
    # each selected area's current ratio to its station-specific danger level.
    rain_points = 35 if max_rain is not None and max_rain >= 60 else 20 if max_rain is not None and max_rain >= 30 else 10 if max_rain is not None and max_rain >= 10 else 0
    level_points = {"danger": 60, "warning": 45, "alert": 25, "normal": 0}[stage_status]
    score = min(100, rain_points + level_points)
    if stage_status == "danger":
        score = max(70, score)
    label = "High" if stage_status == "danger" or score >= 70 else "Elevated" if stage_status == "warning" or score >= 45 else "Watch" if stage_status == "alert" or score >= 20 else "Low"
    if label == "High" and stage_status == "danger":
        indicator = "DANGER INDICATOR"
        message = "At least one selected station is at or above its danger threshold in this historical demo snapshot."
        guidance = ["Check current JPS and local authority alerts for the area.", "Avoid flooded roads, riverbanks, and moving water.", "Be ready to follow official instructions to move to a safer place."]
    elif label == "High":
        indicator = "HIGH DEMO OUTLOOK"
        message = "The rainfall estimate and selected river readings combine to a high demo outlook; at least one station is at warning level, but none is at danger level." if stage_status == "warning" else "The rainfall estimate and selected river readings combine to a high demo outlook; no station is currently at its danger threshold in this snapshot."
        guidance = ["Check current JPS and local authority alerts before making safety decisions.", "Monitor nearby river stations and rainfall closely.", "Review a safe route and household or site response plan."]
    elif label == "Elevated":
        indicator = "WARNING INDICATOR" if stage_status == "warning" else "ELEVATED OUTLOOK"
        message = "At least one selected station is at or above its warning threshold." if stage_status == "warning" else "The selected rainfall estimate and river readings show an elevated demo outlook."
        guidance = ["Check current official advisories and monitor the selected area.", "Review your household or site flood-response plan.", "Avoid routes that become unsafe if water rises."]
    elif label == "Watch":
        indicator = "MONITOR CONDITIONS"
        message = "At least one selected station is at or above its alert threshold." if stage_status == "alert" else "The demo outlook suggests closer monitoring of rainfall and river levels."
        guidance = ["Check rainfall and water-level updates for the selected area.", "Check official advisories if rain intensifies or levels rise.", "Keep accessible drains clear only where it is safe to do so."]
    else:
        indicator = "NO ELEVATED INDICATOR"
        message = "No elevated indicator appears in the selected historical demo data. This is not an all-clear for current conditions."
        guidance = ["Continue routine monitoring.", "Check current official advisories before travel or other safety decisions."]
    return {
        "label": label, "indicator": indicator, "message": message, "water_level_status": stage_status,
        "score": score, "forecast_date": "2026-11-12",
        "station_forecasts": len(forecasts), "max_predicted_rain_mm": round(max_rain, 1) if max_rain is not None else None,
        "average_predicted_rain_mm": round(avg_rain, 1) if avg_rain is not None else None,
        "max_water_danger_ratio": round(max_ratio, 3) if max_ratio is not None else None,
        "max_water_level_m": max_stage, "threshold_for_max_level_m": max_danger,
        "guidance": guidance,
        "basis": "The score combines a five-day rainfall estimate with station-specific alert, warning, and danger thresholds.",
    }
