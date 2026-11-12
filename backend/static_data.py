"""
Static data embedded for Vercel deployment
This avoids filesystem dependencies in serverless environment
"""

import json

# Load station data
STATIONS_DATA = [
  {
    "station_id": "S07",
    "station_name": "Lornie Road",
    "station_device_id": "S07",
    "location_longitude": 103.8334,
    "location_latitude": 1.3415
  },
  {
    "station_id": "S08",
    "station_name": "Upper Thomson Road",
    "station_device_id": "S08",
    "location_longitude": 103.8271,
    "location_latitude": 1.3701
  },
  {
    "station_id": "S104",
    "station_name": "Woodlands Avenue 9",
    "station_device_id": "S104",
    "location_longitude": 103.78538,
    "location_latitude": 1.44387
  },
  {
    "station_id": "S107",
    "station_name": "East Coast Parkway",
    "station_device_id": "S107",
    "location_longitude": 103.9625,
    "location_latitude": 1.3135
  },
  {
    "station_id": "S109",
    "station_name": "Ang Mo Kio Avenue 5",
    "station_device_id": "S109",
    "location_longitude": 103.8492,
    "location_latitude": 1.3764
  },
  {
    "station_id": "S111",
    "station_name": "Scotts Road",
    "station_device_id": "S111",
    "location_longitude": 103.8365,
    "location_latitude": 1.31055
  },
  {
    "station_id": "S113",
    "station_name": "Marine Parade Road",
    "station_device_id": "S113",
    "location_longitude": 103.9104,
    "location_latitude": 1.30648
  },
  {
    "station_id": "S116",
    "station_name": "West Coast Highway",
    "station_device_id": "S116",
    "location_longitude": 103.754,
    "location_latitude": 1.281
  },
  {
    "station_id": "S24",
    "station_name": "Upper Changi Road North",
    "station_device_id": "S24",
    "location_longitude": 103.9826,
    "location_latitude": 1.3678
  },
  {
    "station_id": "S50",
    "station_name": "Clementi Road",
    "station_device_id": "S50",
    "location_longitude": 103.7768,
    "location_latitude": 1.3337
  }
]

SENSORS_DATA = [
  {
    "station_id": "CWS186",
    "station_name": "Eng Neo Ave OD (Vanda Lk u/s culvert)",
    "x_svy21": 24084.32,
    "y_svy21": 34974.36,
    "longitude": 103.798134,
    "latitude": 1.33257
  },
  {
    "station_id": "CWS192",
    "station_name": "Happy Ave OD (Jln Gembira)",
    "x_svy21": 33422.30,
    "y_svy21": 34953.96,
    "longitude": 103.882041,
    "latitude": 1.332385
  },
  {
    "station_id": "EWS101",
    "station_name": "Upp East Coast Rd/Parbury Ave (Riveria Residences)",
    "x_svy21": 40212.83,
    "y_svy21": 33094.83,
    "longitude": 103.943057,
    "latitude": 1.31557
  },
  {
    "station_id": "WWS122",
    "station_name": "Boon Lay Way (Blk 201)",
    "x_svy21": 14912.88,
    "y_svy21": 36127.73,
    "longitude": 103.715723,
    "latitude": 1.343
  },
  {
    "station_id": "WWS134",
    "station_name": "Bukit Timah Rd/ Blackmore Dr",
    "x_svy21": 22454.75,
    "y_svy21": 35289.01,
    "longitude": 103.783491,
    "latitude": 1.335415
  }
]

def get_stations():
    """Get all rainfall stations"""
    return STATIONS_DATA

def get_sensors():
    """Get all PUB sensors"""
    return SENSORS_DATA
