"""
Vercel serverless function entry point
"""
from mangum import Mangum
from main import app

# Wrap FastAPI app for AWS Lambda / Vercel
handler = Mangum(app, lifespan="off")
