"""
Vercel serverless function entry point
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from mangum import Mangum
from fastapi import FastAPI
from main import app as backend_app

# Create wrapper that mounts backend at /api
app = FastAPI()
app.mount("/api", backend_app)

# Wrap for Vercel
handler = Mangum(app, lifespan="off")
