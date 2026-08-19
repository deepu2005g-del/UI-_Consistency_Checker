"""
FastAPI application entry point.
AI-Powered UI Consistency Checker Backend.
"""

import logging
import sys
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes_analysis import router as analysis_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")

    # Ensure uploads directory exists
    Path("uploads").mkdir(parents=True, exist_ok=True)

    # Log config (without secrets)
    logger.info(f"CORS origins: {settings.FRONTEND_URL}")
    logger.info(f"Gemini API key configured: {'Yes' if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != 'your_gemini_api_key_here' else 'No'}")
    logger.info(f"MongoDB URI configured: {'Yes' if settings.MONGODB_URI else 'No (using in-memory storage)'}")

    yield

    # Shutdown
    logger.info("Shutting down")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "An AI-powered tool that analyzes web application UIs for visual consistency. "
        "Accepts screenshots or live website URLs and generates detailed consistency reports "
        "with scores, issue detection, and AI-powered fix recommendations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
        "https://ui-consistency-checker-sigma.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for serving screenshots
uploads_path = Path("uploads")
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(analysis_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "ai_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
        "mongodb_configured": bool(settings.MONGODB_URI),
    }

if __name__ == "__main__":
    import uvicorn
    # Run without reload on Windows to prevent event loop issues with Playwright
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
