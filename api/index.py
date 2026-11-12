"""
Vercel serverless function entry point
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from mangum import Mangum
from fastapi import FastAPI, Request
from fastapi.responses import Response
from main import app as backend_app

# Create a wrapper app that handles /api prefix
app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(request: Request, path: str):
    # Strip /api prefix if present
    if path.startswith("api/"):
        path = path[4:]  # Remove "api/"
    elif path == "api":
        path = ""
    
    # Forward to backend app with modified path
    scope = dict(request.scope)
    scope["path"] = "/" + path if path else "/"
    
    # Call the backend app
    from starlette.testclient import TestClient
    client = TestClient(backend_app)
    
    method = request.method.lower()
    url = "/" + path
    headers = dict(request.headers)
    
    if method == "get":
        response = client.get(url, headers=headers, params=dict(request.query_params))
    elif method == "post":
        body = await request.body()
        response = client.post(url, headers=headers, content=body)
    else:
        response = client.request(method, url, headers=headers)
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

# Wrap for Vercel
handler = Mangum(app, lifespan="off")
