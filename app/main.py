import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all API routers from the organized package
from app.api import (
    superset_router,
    debug_router,
    generate_router,
    export_router
)

from app.utils.logging import init_app_logging

# Initialize comprehensive logging
init_app_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Assisted Dashboard & Chart Generator for Apache Superset",
    description="An AI Orchestrator to generate Superset dashboards from natural language.",
    version="0.1.0",
)

# Add CORS middleware to enable frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",    # Angular dev server
        "http://127.0.0.1:4200",   # Alternative localhost
        "http://localhost:3000",   # Alternative frontend port
        "http://127.0.0.1:3000",   # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Root endpoint with application status."""
    logger.info("Root endpoint accessed - Superset AI Orchestrator is running")
    return {
        "message": "Welcome to the Superset AI Orchestrator",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-01-08T00:00:00Z"  # Would be dynamic in real app
    }

# Include all API routers with proper prefixes and tags
app.include_router(
    superset_router,
    prefix="/v1",
    tags=["Superset Resources"]
)

app.include_router(
    debug_router,
    prefix="/v1",
    tags=["Debug & Monitoring"]
)

app.include_router(
    generate_router,
    prefix="/v1",
    tags=["AI Generation"]
)

app.include_router(
    export_router,
    prefix="/v1",
    tags=["Chart Export"]
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("🎯 Superset AI Orchestrator starting up...")
    logger.info("📚 API documentation available at: /docs")
    logger.info("🔍 Alternative docs available at: /redoc")
    logger.info("🏥 Health check available at: /health")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("🛑 Superset AI Orchestrator shutting down...")

logger.info("🎯 Application configuration complete - All routes registered")
