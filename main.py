"""
Quest Beyond -- FastAPI Backend
Serves all patient, dashboard, timeline, alerts, devices, forecast, genie,
family and reports data consumed by the React front-end.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, auth, connect, devices, family, google_health, integrations, patients, reports, vertex_chat

app = FastAPI(
    title="Quest Beyond API",
    description="Patient health data aggregation API for Quest Beyond",
    version="1.0.0",
)

_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
# In Cloud Run, set ALLOW_ORIGINS="https://your-frontend.com,https://other.com"
_extra = [o.strip() for o in os.environ.get("ALLOW_ORIGINS", "").split(",") if o.strip()]
_origins = _DEFAULT_ORIGINS + _extra

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router registration

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(family.router)
app.include_router(reports.router)
app.include_router(devices.router)
app.include_router(admin.router)
app.include_router(integrations.router)
app.include_router(connect.router)
app.include_router(google_health.router)
app.include_router(vertex_chat.router)


@app.get("/")
def root() -> dict:
    """Root endpoint - provides API information and links to documentation."""
    return {
        "service": "Quest Beyond API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
        "health_check": "/health"
    }


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy", "service": "quest-beyond-api", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
