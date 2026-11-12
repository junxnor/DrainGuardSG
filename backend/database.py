"""
Database operations for DrainGuard Singapore
PostgreSQL with SQLAlchemy for Vercel deployment
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, select, func
from dotenv import load_dotenv
from static_data import STATIONS_DATA, SENSORS_DATA
import random

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning("DATABASE_URL not set, using in-memory fallback")
    USE_DATABASE = False
    rainfall_readings_cache = []
else:
    USE_DATABASE = True
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# SQLAlchemy Base
Base = declarative_base()

# Database Models
class Station(Base):
    __tablename__ = "stations"
    
    station_id = Column(String, primary_key=True)
    station_name = Column(String, nullable=False)
    device_id = Column(String)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Sensor(Base):
    __tablename__ = "sensors"
    
    station_id = Column(String, primary_key=True)
    station_name = Column(String, nullable=False)
    x_svy21 = Column(Float)
    y_svy21 = Column(Float)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RainfallReading(Base):
    __tablename__ = "rainfall_readings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    station_id = Column(String, nullable=False, index=True)
    station_name = Column(String)
    longitude = Column(Float)
    latitude = Column(Float)
    reading_value = Column(Float, nullable=False, index=True)
    reading_unit = Column(String, default="mm")
    created_at = Column(DateTime, default=datetime.utcnow)

async def init_database():
    """Initialize database and create tables"""
    if not USE_DATABASE:
        logger.info("Using in-memory storage (no DATABASE_URL set)")
        await generate_sample_rainfall_data()
        return
    
    try:
        logger.info("Initializing PostgreSQL database...")
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
        
        # Load reference data if tables are empty
        await load_reference_data()
        
        # Generate sample rainfall data if needed
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(RainfallReading.id)))
            count = result.scalar()
            if count == 0:
                logger.info("No rainfall data found, generating sample data...")
                await generate_sample_rainfall_data_db()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def load_reference_data():
    """Load stations and sensors from static data if tables are empty"""
    if not USE_DATABASE:
        return
        
    try:
        async with AsyncSessionLocal() as session:
            # Check if stations exist
            result = await session.execute(select(func.count(Station.station_id)))
            count = result.scalar()
            
            if count == 0:
                logger.info("Loading stations from static data...")
                for station_data in STATIONS_DATA:
                    station = Station(
                        station_id=station_data["station_id"],
                        station_name=station_data["station_name"],
                        device_id=station_data.get("station_device_id"),
                        longitude=station_data["location_longitude"],
                        latitude=station_data["location_latitude"]
                    )
                    session.add(station)
                await session.commit()
                logger.info(f"Loaded {len(STATIONS_DATA)} stations")
            
            # Check if sensors exist
            result = await session.execute(select(func.count(Sensor.station_id)))
            count = result.scalar()
            
            if count == 0:
                logger.info("Loading sensors from static data...")
                for sensor_data in SENSORS_DATA:
                    sensor = Sensor(
                        station_id=sensor_data["station_id"],
                        station_name=sensor_data["station_name"],
                        x_svy21=sensor_data.get("x_svy21"),
                        y_svy21=sensor_data.get("y_svy21"),
                        longitude=sensor_data["longitude"],
                        latitude=sensor_data["latitude"]
                    )
                    session.add(sensor)
                await session.commit()
                logger.info(f"Loaded {len(SENSORS_DATA)} sensors")
                
    except Exception as e:
        logger.error(f"Failed to load reference data: {e}")

async def generate_sample_rainfall_data():
    """Generate sample rainfall data for in-memory demo"""
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
                "reading_value": round(random.uniform(0, 25), 1),
                "reading_unit": "mm",
                "created_at": timestamp.isoformat()
            }
            rainfall_readings_cache.append(reading)

async def generate_sample_rainfall_data_db():
    """Generate sample rainfall data for database"""
    if not USE_DATABASE:
        await generate_sample_rainfall_data()
        return
    
    try:
        async with AsyncSessionLocal() as session:
            readings = []
            # Generate last 48 hours of data
            for hours_ago in range(48, 0, -1):
                timestamp = datetime.now() - timedelta(hours=hours_ago)
                
                # Add readings for first 5 stations
                for station in STATIONS_DATA[:5]:
                    reading = RainfallReading(
                        timestamp=timestamp,
                        station_id=station["station_id"],
                        station_name=station["station_name"],
                        longitude=station["location_longitude"],
                        latitude=station["location_latitude"],
                        reading_value=round(random.uniform(0, 25), 1),
                        reading_unit="mm"
                    )
                    readings.append(reading)
            
            session.add_all(readings)
            await session.commit()
            logger.info(f"Generated {len(readings)} sample rainfall readings")
    except Exception as e:
        logger.error(f"Failed to generate sample data: {e}")

async def get_all_stations() -> List[Dict[str, Any]]:
    """Get all rainfall stations"""
    if not USE_DATABASE:
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
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Station).order_by(Station.station_id))
            stations = result.scalars().all()
            return [
                {
                    "station_id": s.station_id,
                    "station_name": s.station_name,
                    "device_id": s.device_id,
                    "longitude": s.longitude,
                    "latitude": s.latitude
                }
                for s in stations
            ]
    except Exception as e:
        logger.error(f"Failed to get stations: {e}")
        return []

async def get_all_sensors() -> List[Dict[str, Any]]:
    """Get all PUB sensors"""
    if not USE_DATABASE:
        return SENSORS_DATA
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Sensor).order_by(Sensor.station_id))
            sensors = result.scalars().all()
            return [
                {
                    "station_id": s.station_id,
                    "station_name": s.station_name,
                    "x_svy21": s.x_svy21,
                    "y_svy21": s.y_svy21,
                    "longitude": s.longitude,
                    "latitude": s.latitude
                }
                for s in sensors
            ]
    except Exception as e:
        logger.error(f"Failed to get sensors: {e}")
        return []

async def get_latest_rainfall(limit: int = 100) -> List[Dict[str, Any]]:
    """Get latest rainfall readings"""
    if not USE_DATABASE:
        return sorted(rainfall_readings_cache, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RainfallReading)
                .order_by(RainfallReading.timestamp.desc())
                .limit(limit)
            )
            readings = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat(),
                    "station_id": r.station_id,
                    "station_name": r.station_name,
                    "longitude": r.longitude,
                    "latitude": r.latitude,
                    "reading_value": r.reading_value,
                    "reading_unit": r.reading_unit
                }
                for r in readings
            ]
    except Exception as e:
        logger.error(f"Failed to get rainfall: {e}")
        return []

async def get_rainfall_by_timerange(
    start_time: datetime,
    end_time: datetime,
    station_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get rainfall readings within time range"""
    if not USE_DATABASE:
        results = [
            r for r in rainfall_readings_cache
            if start_time.isoformat() <= r["timestamp"] <= end_time.isoformat()
        ]
        if station_id:
            results = [r for r in results if r["station_id"] == station_id]
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)
    
    try:
        async with AsyncSessionLocal() as session:
            query = select(RainfallReading).where(
                RainfallReading.timestamp.between(start_time, end_time)
            )
            if station_id:
                query = query.where(RainfallReading.station_id == station_id)
            query = query.order_by(RainfallReading.timestamp.desc())
            
            result = await session.execute(query)
            readings = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat(),
                    "station_id": r.station_id,
                    "station_name": r.station_name,
                    "longitude": r.longitude,
                    "latitude": r.latitude,
                    "reading_value": r.reading_value,
                    "reading_unit": r.reading_unit
                }
                for r in readings
            ]
    except Exception as e:
        logger.error(f"Failed to get rainfall by timerange: {e}")
        return []

async def insert_rainfall_readings(readings: List[Dict[str, Any]]):
    """Insert rainfall readings into database"""
    if not USE_DATABASE:
        global rainfall_readings_cache
        for reading in readings:
            reading["id"] = len(rainfall_readings_cache) + 1
            reading["created_at"] = datetime.now().isoformat()
            rainfall_readings_cache.append(reading)
        logger.info(f"Inserted {len(readings)} rainfall readings to cache")
        return
    
    try:
        async with AsyncSessionLocal() as session:
            db_readings = []
            for reading in readings:
                db_reading = RainfallReading(
                    timestamp=datetime.fromisoformat(reading["timestamp"]) if isinstance(reading["timestamp"], str) else reading["timestamp"],
                    station_id=reading["station_id"],
                    station_name=reading.get("station_name"),
                    longitude=reading.get("longitude"),
                    latitude=reading.get("latitude"),
                    reading_value=reading["reading_value"],
                    reading_unit=reading.get("reading_unit", "mm")
                )
                db_readings.append(db_reading)
            
            session.add_all(db_readings)
            await session.commit()
            logger.info(f"Inserted {len(readings)} rainfall readings to database")
    except Exception as e:
        logger.error(f"Failed to insert rainfall readings: {e}")
