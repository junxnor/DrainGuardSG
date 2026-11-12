"""
Recommendations API Router
Endpoints for preventive recommendations
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel

router = APIRouter()

class Recommendation(BaseModel):
    category: str
    priority: str
    title: str
    description: str
    icon: str

def get_recommendations_by_risk(risk_level: str) -> List[Recommendation]:
    """Generate recommendations based on risk level"""
    
    base_recommendations = [
        Recommendation(
            category="monitoring",
            priority="high",
            title="Monitor Official PUB Alerts",
            description="Check PUB's official channels for flash flood warnings and updates",
            icon="alert-circle"
        ),
        Recommendation(
            category="information",
            priority="medium",
            title="Stay Informed",
            description="Keep updated with latest rainfall and flood risk information",
            icon="info"
        )
    ]
    
    if risk_level.lower() in ["critical", "high"]:
        return [
            Recommendation(
                category="safety",
                priority="critical",
                title="Avoid Flood-Prone Areas",
                description="Stay away from known flood-prone locations and low-lying areas",
                icon="alert-triangle"
            ),
            Recommendation(
                category="safety",
                priority="critical",
                title="Do Not Drive Through Flooded Roads",
                description="Turn around, don't drown. Never attempt to drive through standing water",
                icon="car"
            ),
            Recommendation(
                category="preparation",
                priority="high",
                title="Prepare Emergency Supplies",
                description="Keep emergency supplies ready including torches, batteries, and first aid kit",
                icon="package"
            ),
            Recommendation(
                category="drainage",
                priority="high",
                title="Clear Drainage Systems",
                description="Ensure drains and gutters near your premises are clear of debris",
                icon="droplet"
            ),
            *base_recommendations
        ]
    
    elif risk_level.lower() == "moderate":
        return [
            Recommendation(
                category="awareness",
                priority="medium",
                title="Exercise Caution",
                description="Be alert for sudden changes in weather and rainfall intensity",
                icon="eye"
            ),
            Recommendation(
                category="planning",
                priority="medium",
                title="Plan Alternative Routes",
                description="Identify alternative routes in case of road closures due to flooding",
                icon="map"
            ),
            Recommendation(
                category="drainage",
                priority="medium",
                title="Check Drainage",
                description="Inspect and clear drains around your property if possible",
                icon="droplet"
            ),
            *base_recommendations
        ]
    
    else:  # Low risk
        return [
            Recommendation(
                category="routine",
                priority="low",
                title="Regular Monitoring",
                description="Continue routine monitoring of weather conditions",
                icon="cloud"
            ),
            Recommendation(
                category="maintenance",
                priority="low",
                title="Drainage Maintenance",
                description="Regular maintenance of drainage systems helps prevent future flooding",
                icon="tool"
            ),
            *base_recommendations
        ]

@router.get("/", response_model=List[Recommendation])
async def get_recommendations(
    risk_level: str = Query(default="moderate", description="Risk level: low, moderate, high, critical")
):
    """
    Get preventive recommendations based on risk level
    
    - **risk_level**: Current risk level (low, moderate, high, critical)
    """
    try:
        valid_levels = ["low", "moderate", "high", "critical"]
        if risk_level.lower() not in valid_levels:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid risk level. Must be one of: {', '.join(valid_levels)}"
            )
        
        recommendations = get_recommendations_by_risk(risk_level)
        return recommendations
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

@router.get("/all")
async def get_all_recommendations():
    """
    Get all recommendations for all risk levels
    """
    return {
        "low": get_recommendations_by_risk("low"),
        "moderate": get_recommendations_by_risk("moderate"),
        "high": get_recommendations_by_risk("high"),
        "critical": get_recommendations_by_risk("critical")
    }
