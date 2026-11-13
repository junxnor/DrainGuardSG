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
import random
import math

# Import static data only if needed for fallback
try:
    from static_data import STATIONS_DATA, SENSORS_DATA
except ImportError:
    STATIONS_DATA = []
    SENSORS_DATA = []

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def _normalize_database_url(raw: Optional[str]) -> Optional[str]:
    """Clean common copy/paste mistakes and force the asyncpg driver."""
    if not raw:
        return None
    url = raw.strip().strip('"').strip("'").strip()
    for prefix in ("postgres://", "postgresql://", "postgresql+psycopg2://", "postgresql+psycopg://"):
        if url.startswith(prefix):
            url = "postgresql+asyncpg://" + url[len(prefix):]
            break
    return url or None

# Database URL from environment variable
DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL"))
DATABASE_ERROR: Optional[str] = None  # Reported by /health; never contains the URL itself
rainfall_readings_cache = []

USE_DATABASE = False
if not DATABASE_URL:
    DATABASE_ERROR = "DATABASE_URL is not set"
    logger.warning("DATABASE_URL not set, using in-memory fallback")
else:
    try:
        engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        USE_DATABASE = True
    except Exception as e:
        # Keep the app running so /health can report the problem instead of crashing
        DATABASE_ERROR = f"Invalid DATABASE_URL: {type(e).__name__}"
        logger.error(DATABASE_ERROR)

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

class PubWaterLevelSensor(Base):
    """Model for the pub_water_level_sensors table (328 sensors)"""
    __tablename__ = "pub_water_level_sensors"
    
    station_id = Column("Station ID", String, primary_key=True)
    station_name = Column("Station Name", String, nullable=False)
    x = Column("X", Float)  # SVY21 X coordinate
    y = Column("Y", Float)  # SVY21 Y coordinate

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

def svy21_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """
    Convert SVY21 (EPSG:3414) easting/northing to WGS84 (longitude, latitude).
    Exact inverse Transverse Mercator projection with SVY21 parameters
    (WGS84 ellipsoid, origin 1°22'N 103°50'E, scale 1.0,
    false easting 28001.642 m, false northing 38744.572 m).
    """
    a = 6378137.0
    f = 1 / 298.257223563
    lat0 = math.radians(1 + 22 / 60)
    lon0 = math.radians(103 + 50 / 60)
    k0 = 1.0
    false_n, false_e = 38744.572, 28001.642

    e2 = 2 * f - f * f
    e4, e6 = e2 * e2, e2 * e2 * e2
    n = (a - a * math.sqrt(1 - e2)) / (a + a * math.sqrt(1 - e2))
    n2, n3, n4 = n ** 2, n ** 3, n ** 4
    g = a * (1 - n) * (1 - n2) * (1 + 9 * n2 / 4 + 225 * n4 / 64) * (math.pi / 180)

    def meridian(lat: float) -> float:
        a0 = 1 - e2 / 4 - 3 * e4 / 64 - 5 * e6 / 256
        a2 = 3 / 8 * (e2 + e4 / 4 + 15 * e6 / 128)
        a4 = 15 / 256 * (e4 + 3 * e6 / 4)
        a6 = 35 * e6 / 3072
        return a * (a0 * lat - a2 * math.sin(2 * lat) + a4 * math.sin(4 * lat) - a6 * math.sin(6 * lat))

    m = (y - false_n) / k0 + meridian(lat0)
    sigma = math.radians(m / g)
    lat_p = (
        sigma
        + (3 * n / 2 - 27 * n3 / 32) * math.sin(2 * sigma)
        + (21 * n2 / 16 - 55 * n4 / 32) * math.sin(4 * sigma)
        + (151 * n3 / 96) * math.sin(6 * sigma)
        + (1097 * n4 / 512) * math.sin(8 * sigma)
    )

    sin_p = math.sin(lat_p)
    rho = a * (1 - e2) / (1 - e2 * sin_p ** 2) ** 1.5
    nu = a / math.sqrt(1 - e2 * sin_p ** 2)
    psi = nu / rho
    t = math.tan(lat_p)
    e_ = x - false_e
    xk = e_ / (k0 * nu)

    lat = lat_p - (t / (k0 * rho)) * (e_ * xk / 2) \
        + (t / (k0 * rho)) * (e_ * xk ** 3 / 24) * (-4 * psi ** 2 + 9 * psi * (1 - t ** 2) + 12 * t ** 2) \
        - (t / (k0 * rho)) * (e_ * xk ** 5 / 720) * (
            8 * psi ** 4 * (11 - 24 * t ** 2) - 12 * psi ** 3 * (21 - 71 * t ** 2)
            + 15 * psi ** 2 * (15 - 98 * t ** 2 + 15 * t ** 4) + 180 * psi * (5 * t ** 2 - 3 * t ** 4) + 360 * t ** 4
        ) \
        + (t / (k0 * rho)) * (e_ * xk ** 7 / 40320) * (1385 + 3633 * t ** 2 + 4095 * t ** 4 + 1575 * t ** 6)

    sec = 1 / math.cos(lat_p)
    lon = lon0 + xk * sec \
        - xk ** 3 * sec / 6 * (psi + 2 * t ** 2) \
        + xk ** 5 * sec / 120 * (-4 * psi ** 3 * (1 - 6 * t ** 2) + psi ** 2 * (9 - 68 * t ** 2) + 72 * psi * t ** 2 + 24 * t ** 4) \
        - xk ** 7 * sec / 5040 * (61 + 662 * t ** 2 + 1320 * t ** 4 + 720 * t ** 6)

    return math.degrees(lon), math.degrees(lat)

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
    """Get all PUB water level sensors from pub_water_level_sensors table (328 sensors)"""
    if not USE_DATABASE:
        return SENSORS_DATA
    
    try:
        async with AsyncSessionLocal() as session:
            # Query the pub_water_level_sensors table with 328 sensors
            result = await session.execute(
                select(PubWaterLevelSensor).order_by(PubWaterLevelSensor.station_id)
            )
            pub_sensors = result.scalars().all()
            
            # Convert SVY21 coordinates to WGS84 and format response
            sensors_list = []
            for s in pub_sensors:
                lon, lat = svy21_to_wgs84(s.x, s.y)
                sensors_list.append({
                    "station_id": s.station_id,
                    "station_name": s.station_name,
                    "x_svy21": s.x,
                    "y_svy21": s.y,
                    "longitude": lon,
                    "latitude": lat
                })
            
            logger.info(f"Retrieved {len(sensors_list)} sensors from pub_water_level_sensors table")
            return sensors_list
            
    except Exception as e:
        logger.error(f"Failed to get sensors from pub_water_level_sensors: {e}")
        # Fallback to old sensors table if pub table fails
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Sensor).order_by(Sensor.station_id))
                sensors = result.scalars().all()
            logger.warning(f"Falling back to sensors table: {len(sensors)} sensors")
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
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}")
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
