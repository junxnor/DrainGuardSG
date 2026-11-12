"""
DrainGuard Singapore - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import os
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
    description="Rainfall-based urban flood risk monitoring using official data.gov.sg readings",
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

# Add middleware to strip /api prefix from requests
@app.middleware("http")
async def strip_api_prefix(request: Request, call_next):
    """
    Strip /api prefix from incoming requests
    Vercel routes /api/* to this service, but FastAPI routes don't have /api prefix
    """
    path = request.url.path
    if path.startswith("/api/"):
        # Remove /api prefix: /api/sensors -> /sensors
        request.scope["path"] = path[4:]
    elif path == "/api":
        # Root API path: /api -> /
        request.scope["path"] = "/"
    
    response = await call_next(request)
    return response

# Import routers
from routers import rainfall, stations, sensors, risk, recommendations, ingest

# Include routers - Vercel will route /api/* to this service
app.include_router(rainfall.router, prefix="/rainfall", tags=["Rainfall"])
app.include_router(stations.router, prefix="/stations", tags=["Stations"])
app.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
app.include_router(risk.router, prefix="/risk", tags=["Risk Assessment"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    import database
    from routers.ingest import summarize_status
    ingestion = summarize_status(await database.get_ingestion_status())
    return {
        "status": "ok",
        "database_connected": database.USE_DATABASE,
        "database_error": database.DATABASE_ERROR,
        "ingestion": {k: ingestion.get(k) for k in
                      ("state", "healthy", "last_success_at", "latest_observed_at", "consecutive_failures")},
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
    logger.info(f"DATABASE_URL configured: {bool(os.getenv('DATABASE_URL'))}")
    
    # Initialize database
    from database import init_database
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization issue: {e}")
    
    logger.info("DrainGuard Singapore API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down DrainGuard Singapore API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
