"""
Stations API Router
Endpoints for rainfall station information
"""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import get_all_stations

router = APIRouter()

class Station(BaseModel):
    station_id: str
    station_name: str
    device_id: str | None
    longitude: float
    latitude: float

@router.get("", response_model=List[Station])
async def get_stations():
    """
    Get all rainfall monitoring stations
    
    Returns list of stations with coordinates for mapping
    """
    try:
        stations = await get_all_stations()
        return stations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stations: {str(e)}")

@router.get("/{station_id}", response_model=Station)
async def get_station_by_id(station_id: str):
    """
    Get specific station by ID
    """
    try:
        stations = await get_all_stations()
        station = next((s for s in stations if s['station_id'] == station_id), None)
        if not station:
            raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
        return station
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch station: {str(e)}")
