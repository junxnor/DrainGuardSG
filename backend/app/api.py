from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import PILOT, ROOT
from .services.demo_history import DISTRICTS_BY_STATE, flood_outlook, load_demo_history

app = FastAPI(
    title="DrainGuard Demo",
    version="1.0.0",
    description="Historical Klang Valley flood monitoring and demonstration outlook.",
)
app.mount("/static", StaticFiles(directory=str(ROOT / "frontend")), name="static")

demo_rainfall, demo_water_levels, demo_model_metrics = load_demo_history()


@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "historical demo prototype", "scope": PILOT}


@app.get("/api/demo-data")
def demo_data(state: str | None = None, district: str | None = None):
    selected_rain = [row for row in demo_rainfall if (not state or row["state"] == state) and (not district or row["district"] == district)]
    selected_water = [row for row in demo_water_levels if (not state or row["state"] == state) and (not district or row["district"] == district)]
    states = sorted({row["state"] for row in (*demo_rainfall, *demo_water_levels) if row.get("state")})
    districts = sorted({name for state_name, names in DISTRICTS_BY_STATE.items() if not state or state_name == state for name in names})
    summary = {
        "rainfall_stations": len(selected_rain),
        "water_level_stations": len(selected_water),
        "at_warning": sum(1 for row in selected_water if row.get("water_level_m") is not None and row.get("warning_m") is not None and row["water_level_m"] >= row["warning_m"]),
        "at_warning_below_danger": sum(1 for row in selected_water if row.get("water_level_m") is not None and row.get("warning_m") is not None and row["water_level_m"] >= row["warning_m"] and (row.get("danger_m") is None or row["water_level_m"] < row["danger_m"])),
        "at_danger": sum(1 for row in selected_water if row.get("water_level_m") is not None and row.get("danger_m") is not None and row["water_level_m"] >= row["danger_m"]),
    }
    alerts = []
    for row in selected_water:
        level = row.get("water_level_m")
        if level is None:
            continue
        if row.get("danger_m") is not None and level >= row["danger_m"]:
            status, threshold = "Danger", row["danger_m"]
        elif row.get("warning_m") is not None and level >= row["warning_m"]:
            status, threshold = "Warning", row["warning_m"]
        elif row.get("alert_m") is not None and level >= row["alert_m"]:
            status, threshold = "Alert", row["alert_m"]
        else:
            continue
        alerts.append({"status": status, "state": row["state"], "district": row["district"], "station_id": row["station_id"], "station_name": row["station_name"], "water_level_m": level, "threshold_m": threshold})
    alerts.sort(key=lambda row: ({"Danger": 0, "Warning": 1, "Alert": 2}[row["status"]], row["state"], row["district"], row["station_name"]))
    return {
        "states": states,
        "districts": districts,
        "summary": summary,
        "outlook": flood_outlook(selected_rain, selected_water),
        "rainfall": selected_rain,
        "water_levels": selected_water,
        "water_level_alerts": alerts,
        "model": {"name": "Random Forest next-day rainfall estimate", **demo_model_metrics},
        "history_dates": ["2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10", "2026-11-11"],
    }
