"""
Database operations for DrainGuard Singapore
SQLite database with async support
"""

import aiosqlite
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "drainguard.db"

# Ensure data directory exists
DB_PATH.parent.mkdir(exist_ok=True, parents=True)

async def init_database():
    """Initialize database and create tables"""
    logger.info(f"Initializing database at {DB_PATH}")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Create stations table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                station_id TEXT PRIMARY KEY,
                station_name TEXT NOT NULL,
                device_id TEXT,
                longitude REAL NOT NULL,
                latitude REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create sensors table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sensors (
                station_id TEXT PRIMARY KEY,
                station_name TEXT NOT NULL,
                x_svy21 REAL,
                y_svy21 REAL,
                longitude REAL NOT NULL,
                latitude REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create rainfall_readings table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rainfall_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                station_id TEXT NOT NULL,
                station_name TEXT,
                longitude REAL,
                latitude REAL,
                reading_value REAL NOT NULL,
                reading_unit TEXT DEFAULT 'mm',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rainfall_timestamp 
            ON rainfall_readings(timestamp)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rainfall_station 
            ON rainfall_readings(station_id)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rainfall_value 
            ON rainfall_readings(reading_value)
        """)
        
        await db.commit()
        logger.info("Database tables created successfully")
    
    # Load reference data
    await load_reference_data()

async def load_reference_data():
    """Load stations and sensors from processed files"""
    logger.info("Loading reference data...")
    
    processed_dir = Path(__file__).parent.parent / "data" / "processed"
    
    # Load stations
    stations_file = processed_dir / "rainfall_stations.csv"
    if stations_file.exists():
        df_stations = pd.read_csv(stations_file)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM stations")  # Clear existing data
            for _, row in df_stations.iterrows():
                await db.execute("""
                    INSERT INTO stations (station_id, station_name, device_id, longitude, latitude)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['station_id'], row['station_name'], row.get('station_device_id'), 
                      row['location_longitude'], row['location_latitude']))
            await db.commit()
            logger.info(f"Loaded {len(df_stations)} stations")
    else:
        logger.warning(f"Stations file not found: {stations_file}")
    
    # Load sensors
    sensors_file = processed_dir / "pub_sensors_wgs84.csv"
    if sensors_file.exists():
        df_sensors = pd.read_csv(sensors_file)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM sensors")  # Clear existing data
            for _, row in df_sensors.iterrows():
                await db.execute("""
                    INSERT INTO sensors (station_id, station_name, x_svy21, y_svy21, longitude, latitude)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (row['Station ID'], row['Station Name'], row.get('X'), row.get('Y'),
                      row['longitude'], row['latitude']))
            await db.commit()
            logger.info(f"Loaded {len(df_sensors)} sensors")
    else:
        logger.warning(f"Sensors file not found: {sensors_file}")

async def get_all_stations() -> List[Dict[str, Any]]:
    """Get all rainfall stations"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM stations ORDER BY station_id") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_all_sensors() -> List[Dict[str, Any]]:
    """Get all PUB sensors"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM sensors ORDER BY station_id") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_latest_rainfall(limit: int = 100) -> List[Dict[str, Any]]:
    """Get latest rainfall readings"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM rainfall_readings 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_rainfall_by_timerange(
    start_time: datetime,
    end_time: datetime,
    station_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get rainfall readings within time range"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        if station_id:
            query = """
                SELECT * FROM rainfall_readings 
                WHERE timestamp BETWEEN ? AND ? AND station_id = ?
                ORDER BY timestamp DESC
            """
            params = (start_time.isoformat(), end_time.isoformat(), station_id)
        else:
            query = """
                SELECT * FROM rainfall_readings 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """
            params = (start_time.isoformat(), end_time.isoformat())
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def insert_rainfall_readings(readings: List[Dict[str, Any]]):
    """Insert rainfall readings into database"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany("""
            INSERT INTO rainfall_readings 
            (timestamp, station_id, station_name, longitude, latitude, reading_value, reading_unit)
            VALUES (:timestamp, :station_id, :station_name, :longitude, :latitude, :reading_value, :reading_unit)
        """, readings)
        await db.commit()
        logger.info(f"Inserted {len(readings)} rainfall readings")
