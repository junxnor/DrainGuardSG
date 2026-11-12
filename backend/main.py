"""
DrainGuard Singapore - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DrainGuard Singapore API",
    description="AI-Powered Urban Flood Risk Monitoring System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - Allow all origins for deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routers import rainfall, stations, sensors, risk, recommendations

# Include routers - Vercel will route /api/* to this service
app.include_router(rainfall.router, prefix="/rainfall", tags=["Rainfall"])
app.include_router(stations.router, prefix="/stations", tags=["Stations"])
app.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
app.include_router(risk.router, prefix="/risk", tags=["Risk Assessment"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "DrainGuard Singapore API",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DrainGuard Singapore API",
        "docs": "/docs",
        "health": "/health"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting DrainGuard Singapore API for Vercel...")
    
    # Initialize in-memory database
    from database import init_database
    try:
        await init_database()
        logger.info("In-memory database initialized successfully")
    except Exception as e:
        logger.warning(f"Non-critical: Failed to initialize database: {e}")
    
    logger.info("DrainGuard Singapore API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down DrainGuard Singapore API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
