"""
Risk Assessment API Router
Endpoints for rainfall-based risk assessment
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from services.risk_service import calculate_risk_overview, calculate_station_risks, RiskLevel

router = APIRouter()

class StationRisk(BaseModel):
    station_id: str
    station_name: str
    longitude: float
    latitude: float
    risk_level: str  # low | moderate | high | critical | no_data
    risk_score: float
    current_rainfall: float
    rainfall_15min: float
    rainfall_1hr: float
    rainfall_3hr: float
    readings_3hr: int
    data_status: str  # ok | no_data
    data_note: Optional[str] = None
    source: str
    observed_at: Optional[str] = None  # end of newest 5-min reading, Singapore time
    last_updated: Optional[str] = None

class RiskOverview(BaseModel):
    overall_risk: str
    risk_score: float
    high_risk_count: int
    moderate_risk_count: int
    low_risk_count: int
    critical_count: int
    no_data_count: int
    total_stations: int
    stations_with_data: int
    data_status: str
    data_note: Optional[str] = None
    source: str
    last_updated: Optional[str] = None
    high_risk_stations: List[str]
    ingestion_state: str = "unknown"  # ok | stalled | failing | never_succeeded | unknown
    ingestion_last_success_at: Optional[str] = None

@router.get("/overview", response_model=RiskOverview)
async def get_risk_overview():
    """
    Get overall risk assessment summary
    
    Returns aggregated risk metrics across all stations
    """
    try:
        overview = await calculate_risk_overview()
        from database import get_ingestion_status
        from routers.ingest import summarize_status
        ingestion = summarize_status(await get_ingestion_status())
        overview["ingestion_state"] = ingestion["state"]
        overview["ingestion_last_success_at"] = ingestion.get("last_success_at")
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate risk overview: {str(e)}")

@router.get("/locations", response_model=List[StationRisk])
async def get_location_risks():
    """
    Get risk assessment for all station locations
    
    Returns detailed risk scores and levels for each station
    """
    try:
        station_risks = await calculate_station_risks()
        return station_risks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate location risks: {str(e)}")

@router.get("/station/{station_id}")
async def get_station_risk(station_id: str):
    """
    Get risk assessment for specific station
    
    - **station_id**: Station identifier
    """
    try:
        station_risks = await calculate_station_risks()
        station_risk = next((s for s in station_risks if s['station_id'] == station_id), None)
        
        if not station_risk:
            raise HTTPException(status_code=404, detail=f"Risk data not available for station {station_id}")
        
        return station_risk
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate station risk: {str(e)}")
