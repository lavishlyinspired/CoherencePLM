"""FastAPI application for requirements management."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config.config import settings
from backend.logger.logger import logger
from datetime import datetime
from backend.api.routes.project import routers as project_routers
from backend.api.routes.traceability_routes import router as traceability_router
from backend.api.routes.test_case_routes import router as test_case_router

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Requirements Management API with LangGraph and Neo4j"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all project routers
for router in project_routers:
    app.include_router(router, prefix="/project", tags=["projects"])

# Include other routers
app.include_router(traceability_router, prefix="/api", tags=["traceability"])
app.include_router(test_case_router, prefix="/project", tags=["test-cases"])

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")

@app.get("/")
async def root():
    return {
        "message": "Requirements Management API",
        "version": settings.api_version,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}