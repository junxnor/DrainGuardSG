"""
Vercel serverless entry point for FastAPI app
This is the handler that Vercel Services will call
"""
from mangum import Mangum
from main import app

# Create the handler - Mangum will wrap the FastAPI app for serverless
# The middleware in main.py handles stripping the /api prefix
handler = Mangum(app, lifespan="off")
