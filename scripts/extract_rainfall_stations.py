"""
Extract unique rainfall station locations from historical data
Creates a reference file for mapping
"""

import pandas as pd
import json
from pathlib import Path

def extract_stations():
    """Extract unique rainfall stations from 2024 data"""
    
    print("="*80)
    print("Extracting Rainfall Station Locations")
    print("="*80)
    
    # Use 2024 data as reference (most recent complete year)
    input_path = Path("data/raw/HistoricalRainfallacrossSingapore/Historical Rainfall across Singapore (2024).csv")
    
    print(f"\nReading from: {input_path.name}")
    print("(Using first 100,000 rows to extract station info)")
    
    # Read just enough to get all unique stations
    df = pd.read_csv(input_path, nrows=100000)
    
    print(f"Loaded {len(df):,} rows")
    
    # Extract unique stations
    stations = df.groupby('station_id').agg({
        'station_name': 'first',
        'station_device_id': 'first',
        'location_longitude': 'first',
        'location_latitude': 'first'
    }).reset_index()
    
    # Validate coordinates
    valid_lng = stations['location_longitude'].between(103.6, 104.0)
    valid_lat = stations['location_latitude'].between(1.15, 1.47)
    
    if not (valid_lng.all() and valid_lat.all()):
        print(f"\n⚠ Warning: {(~(valid_lng & valid_lat)).sum()} stations with invalid coordinates")
        stations = stations[valid_lng & valid_lat]
    
    print(f"\n✓ Extracted {len(stations)} unique stations")
    print(f"\nCoordinate Ranges:")
    print(f"  Longitude: {stations['location_longitude'].min():.6f} to {stations['location_longitude'].max():.6f}")
    print(f"  Latitude: {stations['location_latitude'].min():.6f} to {stations['location_latitude'].max():.6f}")
    
    # Sample stations
    print(f"\nSample Stations:")
    for _, row in stations.head(5).iterrows():
        print(f"  {row['station_id']}: {row['station_name']} ({row['location_longitude']:.4f}, {row['location_latitude']:.4f})")
    
    # Save processed data
    output_dir = Path("data/processed")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Save as CSV
    csv_path = output_dir / "rainfall_stations.csv"
    stations.to_csv(csv_path, index=False)
    print(f"\n✓ Saved CSV to: {csv_path}")
    
    # Save as JSON for frontend
    stations_json = stations.to_dict('records')
    json_path = output_dir / "rainfall_stations.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(stations_json, f, indent=2)
    print(f"✓ Saved JSON to: {json_path}")
    
    return stations

if __name__ == "__main__":
    stations = extract_stations()
    print("\n" + "="*80)
    print("Extraction Complete!")
    print("="*80)
