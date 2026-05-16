from fastapi import FastAPI
from src.api import api_router

app = FastAPI(
    title="Sémantický index dokumentů",
    description="API pro vektorové vyhledávání v dokumentech",
    version="0.1.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify API status."""
    return {"status": "ok", "message": "Sémantický index API is running"}
