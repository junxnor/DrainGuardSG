"""
Vercel serverless function entry point
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from mangum import Mangum
from main import app

# Wrap FastAPI app for Vercel
handler = Mangum(app, lifespan="off")
