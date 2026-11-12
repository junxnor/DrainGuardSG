"""Train the demonstration next-day rainfall model from the five-day PDF history.

This model predicts the next day's station rainfall from the preceding five daily
totals. It is a short-history prototype input to DrainGuard's district outlook,
not a model trained on observed flood events.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "user_provided_csv" / "rainfall_all_states.csv"
OUTPUT = ROOT / "data" / "processed" / "drainguard_demo_rainfall_model.joblib"
FEATURES = [f"daily_2026_11_{day:02d}_mm" for day in range(6, 11)]
TARGET = "daily_2026_11_11_mm"


def train() -> dict:
    frame = pd.read_csv(INPUT)
    required = {"station_id", *FEATURES, TARGET}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns in {INPUT.name}: {sorted(missing)}")
    frame[[*FEATURES, TARGET]] = frame[[*FEATURES, TARGET]].apply(pd.to_numeric, errors="coerce")
    frame = frame.replace([-9999, -9999.0, np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=["station_id", *FEATURES, TARGET])
    frame = frame[(frame[[*FEATURES, TARGET]] >= 0).all(axis=1)]
    # OCR repeated IDs are excluded from training rather than treated as independent stations.
    duplicate_ids = frame["station_id"].duplicated(keep=False)
    excluded_duplicate_rows = int(duplicate_ids.sum())
    frame = frame.loc[~duplicate_ids].copy()
    if len(frame) < 30:
        raise ValueError(f"Only {len(frame)} complete, unique stations are available; at least 30 are required.")

    x, y, groups = frame[FEATURES], frame[TARGET], frame["station_id"]
    split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(split.split(x, y, groups))
    evaluation_model = RandomForestRegressor(
        n_estimators=300, min_samples_leaf=4, max_features=1.0,
        random_state=42, n_jobs=-1,
    )
    evaluation_model.fit(x.iloc[train_idx], y.iloc[train_idx])
    held_out = evaluation_model.predict(x.iloc[test_idx])
    metrics = {
        "model": "RandomForestRegressor",
        "purpose": "demo next-day daily rainfall estimate",
        "training_feature_dates": ["2026-11-06", "2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10"],
        "training_target_date": "2026-11-11",
        "runtime_feature_dates": ["2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10", "2026-11-11"],
        "samples": int(len(frame)),
        "stations": int(frame.station_id.nunique()),
        "excluded_incomplete_or_missing_rows": int(len(pd.read_csv(INPUT)) - len(frame) - excluded_duplicate_rows),
        "excluded_duplicate_id_rows": excluded_duplicate_rows,
        "held_out_stations": int(len(test_idx)),
        "holdout_mae_mm": round(float(mean_absolute_error(y.iloc[test_idx], held_out)), 3),
        "holdout_rmse_mm": round(float(np.sqrt(mean_squared_error(y.iloc[test_idx], held_out))), 3),
        "holdout_r2": round(float(r2_score(y.iloc[test_idx], held_out)), 3),
        "validation_note": "Station-group holdout on a single six-day snapshot; the score is a prototype diagnostic, not evidence of future-season accuracy.",
    }
    final_model = RandomForestRegressor(
        n_estimators=300, min_samples_leaf=4, max_features=1.0,
        random_state=42, n_jobs=-1,
    )
    final_model.fit(x, y)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final_model, "features": FEATURES, "metrics": metrics}, OUTPUT)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    train()
