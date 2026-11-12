# DrainGuard — Klang Valley demo prototype

A historical flood-monitoring and outlook prototype for Selangor, Kuala Lumpur and Putrajaya. It brings rainfall history, water-level thresholds, a trained rainfall estimate, and practical support guidance into one filtered dashboard. It does not fetch live data or issue official warnings.

## Run locally

Requires Python 3.11+.

```powershell
cd C:\Degree\Hackathon\DrainGuard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn app.api:app --app-dir backend --reload
```

Open http://127.0.0.1:8000. Create the virtual environment and install dependencies only once. Stop the server with `Ctrl+C`.

## Historical demo data and model

The dashboard uses the saved Public InfoBanjir exports in `data/processed/user_provided_csv/`. It shows five daily rainfall values (7–11 Nov 2026), the 12 Nov snapshot fields, and current water-level values with station thresholds. Use the state and district selectors to filter the full page.

The Random Forest regression model estimates next-day daily rainfall from a five-day station rainfall window. DrainGuard combines those estimates with current water-level-to-danger-threshold ratios for a demonstration flood outlook and support guidance. This is a demonstration prototype; the outlook is not an official warning or an observed flood-event prediction.

Rebuild the CSVs from the PDFs in your Downloads folder with:

```powershell
python scripts\convert_publicinfobanjir_pdf_exports.py
```

Retrain the demo model after rebuilding the CSVs with:

```powershell
python scripts\train_demo_rainfall_model.py
```

The model artifact, including held-out station metrics, is stored under `data/processed/`. The current fit uses 206 complete, unique station records. Its metrics describe a station holdout from this short historical window and should not be interpreted as seasonal forecast performance.

## Project structure

- `frontend/`: single-page overview, rainfall and water-level monitoring, prediction and guidance.
- `backend/app/`: FastAPI demo endpoint, saved-data loader, district labels and outlook logic.
- `scripts/`: PDF-to-CSV conversion and model training.
- `data/processed/user_provided_csv/`: per-region and combined CSVs, with source-document and page provenance.
- `documentation/model_methodology.md`: model target, features and evaluation notes.

The backend serves only the dashboard and its demo data. Live-source collectors, uploads, database storage and Docker setup are not part of this prototype.
