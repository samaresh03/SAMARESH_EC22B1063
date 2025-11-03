from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pathlib import Path

from app.api.endpoints import router as api_router
from app.config import LOGGING_CONFIG
from app.models import init_db

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Quant Trading Dashboard API",
    description="REST API for quantitative trading analytics and visualization",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Initialize database on startup
@app.on_event("startup")
async def startup_db_client():
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Initialize database
    init_db()
    logger.info("Database initialized")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": app.version,
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
