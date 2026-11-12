"""
Vercel serverless entry point for FastAPI app
This is the handler that Vercel Services will call
"""
from mangum import Mangum
from main import app

# Create the handler
# api_gateway_base_path tells Mangum to strip /api from incoming requests
handler = Mangum(app, lifespan="off", api_gateway_base_path="/api")
