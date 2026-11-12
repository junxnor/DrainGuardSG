"""
Convert PUB Water Level Sensors from SVY21 to WGS84
Extracts sensor locations and converts coordinates for web mapping
"""

import pandas as pd
from pyproj import Transformer
from pathlib import Path

def convert_sensors():
    """Convert PUB sensor coordinates from SVY21 to WGS84"""
    
    print("="*80)
    print("PUB Water Level Sensors Coordinate Conversion")
    print("="*80)
    
    # Load Excel file
    input_path = Path("data/raw/PUBWaterLevelSensors.xlsx")
    df = pd.read_excel(input_path)
    
    print(f"\nLoaded {len(df)} sensors")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df.head(3))
    
    # Check coordinate ranges
    if 'X' in df.columns and 'Y' in df.columns:
        print(f"\nCoordinate Ranges:")
        print(f"X: {df['X'].min():.2f} to {df['X'].max():.2f}")
        print(f"Y: {df['Y'].min():.2f} to {df['Y'].max():.2f}")
        
        # Determine coordinate system
        if df['X'].min() > 1000:
            print("\n✓ Coordinates appear to be SVY21 (EPSG:3414)")
            print("  Converting to WGS84 (EPSG:4326)...")
            
            # Create transformer
            transformer = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)
            
            # Convert coordinates
            df['longitude'], df['latitude'] = transformer.transform(
                df['X'].values,
                df['Y'].values
            )
            
            print("\n✓ Conversion complete!")
            print(f"\nConverted Coordinate Ranges:")
            print(f"Longitude: {df['longitude'].min():.6f} to {df['longitude'].max():.6f}")
            print(f"Latitude: {df['latitude'].min():.6f} to {df['latitude'].max():.6f}")
            
            # Validate coordinates are within Singapore
            valid_lng = df['longitude'].between(103.6, 104.0)
            valid_lat = df['latitude'].between(1.15, 1.47)
            
            if valid_lng.all() and valid_lat.all():
                print("\n✓ All coordinates within Singapore bounds")
            else:
                print(f"\n⚠ Warning: {(~(valid_lng & valid_lat)).sum()} coordinates outside Singapore bounds")
        else:
            print("\n✓ Coordinates appear to already be in WGS84")
            df['longitude'] = df['X']
            df['latitude'] = df['Y']
    
    # Save processed data
    output_dir = Path("data/processed")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_path = output_dir / "pub_sensors_wgs84.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved to: {output_path}")
    print(f"  Records: {len(df)}")
    
    # Also save as JSON for frontend
    sensors_json = df.to_dict('records')
    import json
    json_path = output_dir / "pub_sensors_wgs84.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(sensors_json, f, indent=2)
    
    print(f"✓ Saved JSON to: {json_path}")
    
    return df

if __name__ == "__main__":
    df = convert_sensors()
    print("\n" + "="*80)
    print("Conversion Complete!")
    print("="*80)
