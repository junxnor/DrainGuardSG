"""
Risk Assessment API Router
Endpoints for rainfall-based risk assessment
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
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
    risk_level: str
    risk_score: float
    current_rainfall: float
    rainfall_1hr: float
    rainfall_3hr: float
    last_updated: str

class RiskOverview(BaseModel):
    overall_risk: str
    risk_score: float
    high_risk_count: int
    moderate_risk_count: int
    low_risk_count: int
    total_stations: int
    last_updated: str
    high_risk_stations: List[str]

@router.get("/overview", response_model=RiskOverview)
async def get_risk_overview():
    """
    Get overall risk assessment summary
    
    Returns aggregated risk metrics across all stations
    """
    try:
        overview = await calculate_risk_overview()
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
