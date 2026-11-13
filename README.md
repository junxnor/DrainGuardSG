# 🌧️ DrainGuard Singapore

**AI-Powered Urban Flood Risk Monitoring System**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178c6.svg)](https://www.typescriptlang.org/)

> **Team MeowMeow** - Built for Singapore's Urban Flood Prevention

---

## 🎯 The Problem

Singapore faces increasing urban flooding risks due to intense rainfall and climate change. While government agencies provide flash flood alerts, there's a critical gap:

- ❌ No real-time, granular risk assessment across 328 drainage points
- ❌ Citizens lack accessible tools for localized flood risk awareness
- ❌ Current systems are reactive, not preventive

## 💡 Our Solution

DrainGuard transforms raw rainfall data into actionable intelligence through:

- ✅ **Real-time monitoring** of 63 NEA rainfall stations + 328 PUB water level sensors
- ✅ **AI-powered risk classification** (Low/Moderate/High/Critical) based on rainfall patterns
- ✅ **Interactive map visualization** with hyperlocal risk levels
- ✅ **Context-aware recommendations** for different risk scenarios
- ✅ **Mobile-responsive dashboard** for emergency access

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   React + TS    │ ───> │   FastAPI + ML   │ ───> │  SQLite + Data  │
│   Frontend      │ <─── │   Backend        │ <─── │  Pipeline       │
└─────────────────┘      └──────────────────┘      └─────────────────┘
  • Leaflet Maps          • 13+ REST APIs           • 328 Sensors
  • Recharts              • Risk Assessment         • 63 Stations
  • Tailwind CSS          • Zustand Store           • SVY21→WGS84
```

### Tech Stack

**Frontend:**
- React 18 + TypeScript + Vite
- Leaflet (Interactive Maps)
- Recharts (Data Visualization)
- Tailwind CSS (Responsive Design)
- Zustand (State Management)

**Backend:**
- FastAPI (Python Web Framework)
- SQLite + aiosqlite (Database)
- Pandas (Data Processing)
- Pyproj (Coordinate Transformation)
- Scikit-learn (ML Risk Model)

**Data Sources:**
- [data.gov.sg](https://data.gov.sg) - Historical Rainfall (2016-2024)
- PUB Singapore - 328 Water Level Sensors
- NEA Singapore - 63 Rainfall Monitoring Stations

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### 1️⃣ Clone Repository

```bash
git clone https://github.com/junxnor/DrainGuard.git
cd DrainGuard
```

### 2️⃣ Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start backend server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at: **http://localhost:8000**  
API Docs: **http://localhost:8000/api/docs**

### 3️⃣ Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: **http://localhost:3000**

### 4️⃣ Load Sample Data (Optional)

```bash
cd scripts

# Convert PUB sensors to WGS84 coordinates
python convert_pub_sensors.py

# Extract rainfall stations
python extract_rainfall_stations.py

# Load 50,000 sample rainfall records
python load_sample_data.py
```

---

## 📊 Features

### 🗺️ Interactive Risk Map
- Color-coded markers for 63 rainfall stations
- 328 PUB water level sensors georeferenced
- Real-time risk level overlay
- Click stations for detailed info

### 📈 Risk Overview Dashboard
- **Overall System Risk Level**
- **Critical Zones Count** (>80mm/hr rainfall)
- **High Risk Areas** (50-80mm/hr rainfall)
- **Active Stations** monitoring status

### 🌧️ Rainfall Visualization
- Top 10 stations by rainfall intensity
- Bar chart with color-coded risk levels
- Real-time data updates every 5 minutes

### 💡 Smart Recommendations
- Context-aware preventive actions
- Priority-based (Critical/High/Medium/Low)
- Categories: Public Safety, Infrastructure, Transportation, Emergency

### 🔔 Risk Classification Algorithm

```python
Risk Level = f(Rainfall Intensity, Duration, Location)

• Critical:  >80mm/hr  → Immediate evacuation areas
• High:      50-80mm/hr → Avoid flood-prone zones
• Moderate:  20-50mm/hr → Monitor conditions
• Low:       <20mm/hr   → Normal operations
```

---

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/stations` | GET | All rainfall stations |
| `/api/sensors` | GET | All PUB water level sensors |
| `/api/rainfall/recent` | GET | Recent rainfall data |
| `/api/rainfall/top` | GET | Top rainfall stations |
| `/api/risk/overview` | GET | Overall risk summary |
| `/api/risk/station/{id}` | GET | Station-specific risk |
| `/api/recommendations` | GET | Risk-based recommendations |

Full API Documentation: **http://localhost:8000/api/docs**

---

## 📁 Project Structure

```
DrainGuard/
├── backend/               # FastAPI Backend
│   ├── main.py           # Application entry point
│   ├── database.py       # Database connection & models
│   ├── routers/          # API route handlers
│   │   ├── rainfall.py
│   │   ├── stations.py
│   │   ├── sensors.py
│   │   ├── risk.py
│   │   └── recommendations.py
│   └── services/         # Business logic
│       └── risk_service.py
├── frontend/             # React Frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   │   ├── MapComponent.tsx
│   │   │   ├── RiskOverview.tsx
│   │   │   ├── RainfallChart.tsx
│   │   │   └── RecommendationsPanel.tsx
│   │   ├── services/     # API client
│   │   │   └── api.ts
│   │   ├── store/        # Zustand state management
│   │   │   └── appStore.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── scripts/              # Data processing scripts
│   ├── convert_pub_sensors.py
│   ├── extract_rainfall_stations.py
│   ├── load_sample_data.py
│   └── train_risk_model.py
├── data/                 # Data directory
│   ├── raw/             # Raw datasets
│   │   ├── PUBWaterLevelSensors.xlsx
│   │   ├── HistoricalRainfallacrossSingapore/
│   │   └── ...
│   └── drainguard.db    # SQLite database
└── models/              # ML model artifacts
```

---

## 🔬 Data Processing Pipeline

### 1. Coordinate Transformation
```python
# Convert PUB's SVY21 (engineering) to WGS84 (web standard)
# 328 sensors: (E, N) → (Longitude, Latitude)
pyproj: EPSG:3414 → EPSG:4326
```

### 2. Station Extraction
```python
# Extract unique rainfall stations from historical data
# 63 stations identified across Singapore
# Aggregate location coordinates from 2016-2024 data
```

### 3. Risk Assessment Model
```python
# Machine Learning: Random Forest Classifier
# Features: rainfall_mm, duration_min, location_zone
# Output: risk_level [Low, Moderate, High, Critical]
```

---

## 🎓 Key Innovation

### Why Risk Estimation, Not Flood Prediction?

Most flood prediction models require **labeled historical flood data** (dates, locations, severity). Singapore's open data provides:
- ✅ Rainfall measurements (comprehensive)
- ✅ Sensor locations (detailed)
- ❌ Historical flood labels (unavailable)

**Our Approach:** Build a deployable system today using **rainfall intensity thresholds** validated by hydrology research:

| Threshold | Classification | Action |
|-----------|---------------|---------|
| >80mm/hr | Critical | Immediate evacuation |
| 50-80mm/hr | High | Avoid flood zones |
| 20-50mm/hr | Moderate | Monitor conditions |
| <20mm/hr | Low | Normal operations |

This makes DrainGuard **immediately operational** with existing government infrastructure.

---

## 🌍 Impact & Scalability

### Immediate Impact
- 🏙️ **5.9M residents** with neighborhood-level risk awareness
- 🚨 **PUB & SCDF** prioritized emergency response
- 💰 **Property damage reduction** through preventive action
- 📊 **Transparent data-driven** urban planning

### Future Roadmap
1. **Phase 2:** Integrate actual PUB real-time API
2. **Phase 3:** Deploy ML flood prediction (when labeled data available)
3. **Phase 4:** Mobile app with push notifications
4. **Phase 5:** Regional expansion (Malaysia, Indonesia, Philippines)

---

## ⚠️ Disclaimer

This system provides **rainfall-based risk estimation**, NOT flood prediction. Risk scores are calculated based on rainfall intensity thresholds and do not represent actual flood forecasts.

**Always refer to official [PUB Flash Flood Alerts](https://www.pub.gov.sg) for authoritative information.**

---

## 👥 Team MeowMeow

Built during **[Hackathon Name]** - [Date]

**Tech Stack:** React • TypeScript • FastAPI • Python • Leaflet • Tailwind CSS • SQLite • Scikit-learn

**Data Source:** data.gov.sg • PUB Singapore • NEA Singapore

---

## 📄 License

This project was built for hackathon purposes. Data sources remain property of Singapore government agencies.

---

## 🙏 Acknowledgments

- **PUB Singapore** - Water level sensor data
- **NEA Singapore** - Rainfall monitoring network
- **data.gov.sg** - Open data platform
- **Community** - Climate resilience advocacy

---

**DrainGuard Singapore © 2026** • Built with ❤️ for Urban Flood Prevention

🌐 [Live Demo](#) • 📹 [Video Demo](#) • 📊 [Pitch Deck](#)
