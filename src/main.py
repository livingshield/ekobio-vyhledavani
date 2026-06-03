import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api import api_router
from src.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Initializing database …")
    init_db()
    logger.info("Database ready.")
    yield


app = FastAPI(
    title="Sémantický index dokumentů",
    description="AI-Powered Semantic Document Search",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS – allow everything for the demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")

# Static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the single-page frontend."""
    return FileResponse(str(STATIC_DIR / "index.html"))
