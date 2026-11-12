"""
Risk Assessment Service
Rainfall-based risk estimation
"""

from enum import Enum
from typing import List, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database import get_all_stations

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

def classify_risk_level(risk_score: float) -> RiskLevel:
    """Classify risk level based on score"""
    if risk_score >= 76:
        return RiskLevel.CRITICAL
    elif risk_score >= 51:
        return RiskLevel.HIGH
    elif risk_score >= 26:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW

def calculate_risk_score(
    current_rainfall: float,
    rainfall_15min: float = 0,
    rainfall_1hr: float = 0,
    rainfall_3hr: float = 0,
    historical_percentile: float = 50
) -> float:
    """
    Calculate risk score based on rainfall metrics
    
    Args:
        current_rainfall: Current 5-minute rainfall (mm)
        rainfall_15min: 15-minute accumulated rainfall (mm)
        rainfall_1hr: 1-hour accumulated rainfall (mm)
        rainfall_3hr: 3-hour accumulated rainfall (mm)
        historical_percentile: Historical percentile (0-100)
    
    Returns:
        Risk score (0-100)
    """
    
    # Base score from current intensity (mm per 5min -> mm/hr)
    intensity_mm_per_hr = current_rainfall * 12  # Convert 5-min to hourly rate
    intensity_score = min(intensity_mm_per_hr / 0.5, 100)  # 50mm/hr = 100 points
    
    # Accumulated rainfall scores
    accum_15min = min((rainfall_15min / 10) * 20, 20)  # 10mm in 15min = 20 points
    accum_1hr = min((rainfall_1hr / 30) * 30, 30)      # 30mm in 1hr = 30 points
    accum_3hr = min((rainfall_3hr / 50) * 20, 20)      # 50mm in 3hr = 20 points
    
    # Historical context score
    percentile_score = (historical_percentile / 100) * 20
    
    # Time-of-day multiplier (simplified - actual implementation would use datetime)
    time_multiplier = 1.0
    
    # Weighted sum
    total_score = (
        intensity_score * 0.35 +
        accum_15min * 0.15 +
        accum_1hr * 0.25 +
        accum_3hr * 0.15 +
        percentile_score * 0.10
    ) * time_multiplier
    
    return min(total_score, 100)

async def calculate_station_risks() -> List[Dict[str, Any]]:
    """
    Calculate risk assessment for all stations
    
    Note: Currently using mock data. In production, this would:
    1. Query latest rainfall readings from database
    2. Calculate rolling windows (15min, 1hr, 3hr)
    3. Calculate historical percentiles
    4. Generate risk scores
    """
    
    stations = await get_all_stations()
    station_risks = []
    
    for station in stations:
        # Mock rainfall data - replace with actual database queries
        # In production: query rainfall_readings table for this station
        current_rainfall = 0.5  # mm in 5 minutes
        rainfall_15min = 1.5    # mm in 15 minutes
        rainfall_1hr = 8.0      # mm in 1 hour
        rainfall_3hr = 15.0     # mm in 3 hours
        
        # Calculate risk score
        risk_score = calculate_risk_score(
            current_rainfall=current_rainfall,
            rainfall_15min=rainfall_15min,
            rainfall_1hr=rainfall_1hr,
            rainfall_3hr=rainfall_3hr,
            historical_percentile=55
        )
        
        # Classify risk level
        risk_level = classify_risk_level(risk_score)
        
        station_risks.append({
            "station_id": station["station_id"],
            "station_name": station["station_name"],
            "longitude": station["longitude"],
            "latitude": station["latitude"],
            "risk_level": risk_level.value,
            "risk_score": round(risk_score, 2),
            "current_rainfall": current_rainfall,
            "rainfall_1hr": rainfall_1hr,
            "rainfall_3hr": rainfall_3hr,
            "last_updated": datetime.now().isoformat()
        })
    
    return station_risks

async def calculate_risk_overview() -> Dict[str, Any]:
    """
    Calculate overall risk assessment summary
    """
    
    station_risks = await calculate_station_risks()
    
    # Count risk levels
    risk_counts = {
        RiskLevel.LOW.value: 0,
        RiskLevel.MODERATE.value: 0,
        RiskLevel.HIGH.value: 0,
        RiskLevel.CRITICAL.value: 0
    }
    
    total_score = 0
    high_risk_stations = []
    
    for risk in station_risks:
        risk_counts[risk["risk_level"]] += 1
        total_score += risk["risk_score"]
        
        if risk["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
            high_risk_stations.append(risk["station_id"])
    
    # Calculate overall risk level
    avg_score = total_score / len(station_risks) if station_risks else 0
    overall_risk = classify_risk_level(avg_score)
    
    # If any station is critical, elevate overall risk
    if risk_counts[RiskLevel.CRITICAL.value] > 0:
        overall_risk = RiskLevel.HIGH  # Elevated but not critical
    
    return {
        "overall_risk": overall_risk.value,
        "risk_score": round(avg_score, 2),
        "high_risk_count": risk_counts[RiskLevel.HIGH.value],
        "moderate_risk_count": risk_counts[RiskLevel.MODERATE.value],
        "low_risk_count": risk_counts[RiskLevel.LOW.value],
        "critical_count": risk_counts[RiskLevel.CRITICAL.value],
        "total_stations": len(station_risks),
        "last_updated": datetime.now().isoformat(),
        "high_risk_stations": high_risk_stations
    }
