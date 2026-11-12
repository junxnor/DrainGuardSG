"""
Rainfall API Router
Endpoints for rainfall data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database import get_latest_rainfall, get_rainfall_by_timerange

router = APIRouter()

class RainfallReading(BaseModel):
    id: int | None = None
    timestamp: str
    station_id: str
    station_name: str | None
    longitude: float | None
    latitude: float | None
    reading_value: float
    reading_unit: str = "mm"

@router.get("/latest", response_model=List[RainfallReading])
async def get_latest_readings(limit: int = Query(default=100, ge=1, le=1000)):
    """
    Get latest rainfall readings across all stations
    
    - **limit**: Number of readings to return (1-1000)
    """
    try:
        readings = await get_latest_rainfall(limit=limit)
        return readings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch rainfall data: {str(e)}")

@router.get("/history")
async def get_historical_readings(
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    station_id: Optional[str] = Query(default=None, description="Filter by station ID")
):
    """
    Get historical rainfall readings
    
    - **start_date**: Start date in YYYY-MM-DD format
    - **end_date**: End date in YYYY-MM-DD format
    - **station_id**: Optional station filter
    """
    try:
        # Default to last 7 days if no dates provided
        if not end_date:
            end_time = datetime.now()
        else:
            end_time = datetime.strptime(end_date, "%Y-%m-%d")
        
        if not start_date:
            start_time = end_time - timedelta(days=7)
        else:
            start_time = datetime.strptime(start_date, "%Y-%m-%d")
        
        readings = await get_rainfall_by_timerange(
            start_time=start_time,
            end_time=end_time,
            station_id=station_id
        )
        
        return {
            "start_date": start_time.isoformat(),
            "end_date": end_time.isoformat(),
            "station_id": station_id,
            "count": len(readings),
            "data": readings
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")

@router.get("/station/{station_id}")
async def get_station_rainfall(
    station_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history (1-168)")
):
    """
    Get rainfall history for specific station
    
    - **station_id**: Station identifier
    - **hours**: Number of hours of history to return (default: 24, max: 168)
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        readings = await get_rainfall_by_timerange(
            start_time=start_time,
            end_time=end_time,
            station_id=station_id
        )
        
        if not readings:
            raise HTTPException(status_code=404, detail=f"No data found for station {station_id}")
        
        return {
            "station_id": station_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "count": len(readings),
            "data": readings
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch station data: {str(e)}")
