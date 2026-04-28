from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from app.api.endpoints import router as api_router
from app.core.config import settings
from app.core.logging import logger
from app.core.database import db

app = FastAPI(
    title=settings.APP_NAME,
    description="A production-ready AI chatbot with OpenAI and Telegram integration.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware - Configurable for production
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")] if allowed_origins_str else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def root_health():
    """Root health check for deployment platforms like Render."""
    return {"status": "healthy", "service": settings.APP_NAME}

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """
    Startup event for the FastAPI application.
    """
    logger.info("Starting up AI Chatbot...")
    await db.connect_to_storage()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event for the FastAPI application.
    """
    logger.info("Shutting down AI Chatbot...")
    await db.close_storage_connection()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
