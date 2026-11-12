"""
Sensors API Router
Endpoints for PUB water level sensor information
"""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database import get_all_sensors

router = APIRouter()

class Sensor(BaseModel):
    station_id: str
    station_name: str
    longitude: float
    latitude: float
    x_svy21: float | None = None
    y_svy21: float | None = None

@router.get("/", response_model=List[Sensor])
async def get_sensors():
    """
    Get all PUB water level sensors
    
    Returns list of sensors with WGS84 coordinates for mapping
    """
    try:
        sensors = await get_all_sensors()
        return sensors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sensors: {str(e)}")

@router.get("/{sensor_id}", response_model=Sensor)
async def get_sensor_by_id(sensor_id: str):
    """
    Get specific sensor by ID
    """
    try:
        sensors = await get_all_sensors()
        sensor = next((s for s in sensors if s['station_id'] == sensor_id), None)
        if not sensor:
            raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")
        return sensor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sensor: {str(e)}")
