import os

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from dotenv import load_dotenv

load_dotenv()

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Vertex AI Session configuration
SESSION_SERVICE_URI = ""
# Example allowed origins for CORS
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

print(f"gs://{os.environ.get('GOOGLE_CLOUD_STORAGE_BUCKET')}/artifacts")
# Call the function to get the FastAPI app instance
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    # session_service_uri=SESSION_SERVICE_URI,
    artifact_service_uri=f"gs://{os.environ.get('GOOGLE_CLOUD_STORAGE_BUCKET')}/artifacts",
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# You can add more FastAPI routes or configurations below if needed
@app.get("/hello")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", 8080)))
