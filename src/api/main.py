'''
The Server Entry Point (src/api/main.py)
This file wires everything together and starts the application.
'''

"""
FastAPI Entry Point.
Initializes the application and includes the routers.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.api.routes import router
from src.shared.config import settings
from src.shared.database import DatabaseService

app = FastAPI(
    title="CrewAI Financial Analyst API",
    description="A Production-Grade Agentic API for Stock Analysis.",
    version="1.0.0"
)

# Include our analysis routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
def health_check():
    """Report API liveness and whether at least one worker heartbeat is active."""
    try:
        db = DatabaseService()
        workers_available = db.has_active_workers(settings.worker_active_within_seconds)
        status_value = "healthy" if workers_available else "degraded"
        status_code = 200 if workers_available else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "status": status_value,
                "service": "Financial Analyst Crew",
                "workers_available": workers_available,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "Financial Analyst Crew",
                "detail": str(e),
            },
        )
