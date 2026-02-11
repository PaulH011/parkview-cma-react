"""
Parkview CMA API - FastAPI Backend

This API wraps the ra_stress_tool calculation engine to provide
REST endpoints for the React frontend.

Run with: uvicorn api.main:app --reload --port 8000
Or from api directory: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path so we can import ra_stress_tool
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from api.routes import calculate, defaults, admin
from api.config import CORS_ORIGINS, DEBUG

# Create FastAPI app
app = FastAPI(
    title="Parkview CMA API",
    description="""
## Capital Market Expectations Calculation Engine

This API provides endpoints for calculating expected returns across asset classes
using the Research Affiliates methodology.

### Key Endpoints:
- `/api/calculate/full` - Run full CME calculation
- `/api/calculate/macro-preview` - Lightweight macro preview (for real-time UI)
- `/api/defaults/all` - Get all default input values
### Authentication:
Admin endpoints require the super-user email header.
    """,
    version="1.0.0",
    docs_url="/docs" if DEBUG else None,  # Disable Swagger in production
    redoc_url="/redoc" if DEBUG else None,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    calculate.router,
    prefix="/api/calculate",
    tags=["Calculations"]
)
app.include_router(
    defaults.router,
    prefix="/api/defaults",
    tags=["Defaults"]
)
app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Admin"]
)


@app.get("/", tags=["Health"])
async def root():
    """API root - redirects to docs."""
    return {
        "message": "Parkview CMA API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Used by load balancers and monitoring systems.
    """
    # Verify ra_stress_tool is importable
    try:
        from ra_stress_tool.main import CMEEngine
        engine_ok = True
    except ImportError:
        engine_ok = False

    return {
        "status": "healthy" if engine_ok else "degraded",
        "version": "1.0.0",
        "engine_available": engine_ok
    }


# For running directly with `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )
