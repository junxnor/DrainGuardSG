"""
Database operations for DrainGuard Singapore
Uses in-memory storage for Vercel deployment
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from static_data import STATIONS_DATA, SENSORS_DATA
import random

logger = logging.getLogger(__name__)

# In-memory storage for demo purposes
rainfall_readings_cache = []

async def init_database():
    """Initialize database - for Vercel, this just generates sample data"""
    logger.info("Initializing in-memory database for Vercel deployment...")
    
    # Generate some sample rainfall data
    await generate_sample_rainfall_data()
    
    logger.info(f"Generated {len(rainfall_readings_cache)} sample rainfall readings")

async def generate_sample_rainfall_data():
    """Generate sample rainfall data for demo"""
    global rainfall_readings_cache
    rainfall_readings_cache = []
    
    # Generate last 48 hours of data
    for hours_ago in range(48, 0, -1):
        timestamp = datetime.now() - timedelta(hours=hours_ago)
        
        # Add readings for some stations
        for station in STATIONS_DATA[:5]:  # Just first 5 stations for demo
            reading = {
                "id": len(rainfall_readings_cache) + 1,
                "timestamp": timestamp.isoformat(),
                "station_id": station["station_id"],
                "station_name": station["station_name"],
                "longitude": station["location_longitude"],
                "latitude": station["location_latitude"],
                "reading_value": round(random.uniform(0, 25), 1),  # Random rainfall
                "reading_unit": "mm",
                "created_at": timestamp.isoformat()
            }
            rainfall_readings_cache.append(reading)

async def get_all_stations() -> List[Dict[str, Any]]:
    """Get all rainfall stations"""
    return [
        {
            "station_id": s["station_id"],
            "station_name": s["station_name"],
            "device_id": s.get("station_device_id"),
            "longitude": s["location_longitude"],
            "latitude": s["location_latitude"]
        }
        for s in STATIONS_DATA
    ]

async def get_all_sensors() -> List[Dict[str, Any]]:
    """Get all PUB sensors"""
    return SENSORS_DATA

async def get_latest_rainfall(limit: int = 100) -> List[Dict[str, Any]]:
    """Get latest rainfall readings"""
    return sorted(rainfall_readings_cache, key=lambda x: x["timestamp"], reverse=True)[:limit]

async def get_rainfall_by_timerange(
    start_time: datetime,
    end_time: datetime,
    station_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get rainfall readings within time range"""
    results = [
        r for r in rainfall_readings_cache
        if start_time.isoformat() <= r["timestamp"] <= end_time.isoformat()
    ]
    
    if station_id:
        results = [r for r in results if r["station_id"] == station_id]
    
    return sorted(results, key=lambda x: x["timestamp"], reverse=True)

async def insert_rainfall_readings(readings: List[Dict[str, Any]]):
    """Insert rainfall readings into cache"""
    global rainfall_readings_cache
    for reading in readings:
        reading["id"] = len(rainfall_readings_cache) + 1
        reading["created_at"] = datetime.now().isoformat()
        rainfall_readings_cache.append(reading)
    logger.info(f"Inserted {len(readings)} rainfall readings")
