"""
Load sample rainfall data from 2024 CSV into database
Extracts 2 days of data for demo purposes
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent.parent / "backend"))

def load_sample_data():
    """Load sample rainfall data into database"""
    
    print("="*80)
    print("Loading Sample Rainfall Data")
    print("="*80)
    
    # Path to 2024 rainfall data
    input_file = Path("data/raw/HistoricalRainfallacrossSingapore/Historical Rainfall across Singapore (2024).csv")
    
    print(f"\nReading from: {input_file.name}")
    print("Extracting first 50,000 rows (approximately 2 days of data)...")
    
    # Read sample data
    df = pd.read_csv(input_file, nrows=50000)
    
    print(f"Loaded {len(df):,} rows")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Unique stations: {df['station_id'].nunique()}")
    
    # Parse timestamps
    df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
    
    # Prepare data for database
    df_insert = df[[
        'timestamp', 'station_id', 'station_name', 
        'location_longitude', 'location_latitude', 'reading_value'
    ]].copy()
    
    df_insert.columns = [
        'timestamp', 'station_id', 'station_name', 
        'longitude', 'latitude', 'reading_value'
    ]
    
    df_insert['reading_unit'] = 'mm'
    
    # Connect to database
    db_path = Path("data/drainguard.db")
    conn = sqlite3.connect(db_path)
    
    print(f"\nInserting data into database: {db_path}")
    
    # Insert data
    df_insert.to_sql('rainfall_readings', conn, if_exists='append', index=False)
    
    # Verify insertion
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rainfall_readings")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM rainfall_readings")
    time_range = cursor.fetchone()
    
    conn.close()
    
    print(f"\n✓ Successfully inserted {len(df_insert):,} records")
    print(f"✓ Total records in database: {total_count:,}")
    print(f"✓ Time range: {time_range[0]} to {time_range[1]}")
    
    # Generate statistics
    print(f"\nData Statistics:")
    print(f"  Rainfall readings with value > 0: {(df['reading_value'] > 0).sum():,} ({(df['reading_value'] > 0).sum()/len(df)*100:.1f}%)")
    print(f"  Max rainfall value: {df['reading_value'].max():.2f} mm")
    print(f"  Mean rainfall value: {df['reading_value'].mean():.4f} mm")
    
    # Show sample high rainfall events
    high_rainfall = df[df['reading_value'] > 5].sort_values('reading_value', ascending=False).head(5)
    if len(high_rainfall) > 0:
        print(f"\nTop 5 Rainfall Events:")
        for _, row in high_rainfall.iterrows():
            print(f"  {row['station_name']}: {row['reading_value']:.2f} mm at {row['timestamp']}")
    
    return df

if __name__ == "__main__":
    df = load_sample_data()
    print("\n" + "="*80)
    print("Data Loading Complete!")
    print("="*80)
