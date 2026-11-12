from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PILOT = {
    "Selangor": ["Petaling", "Klang", "Gombak", "Hulu Langat", "Kuala Langat", "Sepang", "Kuala Selangor", "Sabak Bernam", "Hulu Selangor"],
    "Kuala Lumpur": ["Kuala Lumpur"], "Putrajaya": ["Putrajaya"],
}
MALAYSIA_TZ = "Asia/Kuala_Lumpur"
