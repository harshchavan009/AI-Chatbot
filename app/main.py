from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import asyncio
import httpx
import time
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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    # Avoid spamming logs with static file requests
    if not request.url.path.startswith("/assets") and not request.url.path.endswith(".png"):
        logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - {process_time:.4f}s")
    return response

@app.get("/health")
async def root_health():
    """Root health check for deployment platforms like Render."""
    return {"status": "healthy", "service": settings.APP_NAME}

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

async def keep_alive():
    """Background task to ping the service and prevent it from sleeping on free tiers."""
    while True:
        try:
            await asyncio.sleep(840) # 14 minutes (Render sleeps after 15m)
            # Try to get the external URL from environment, fallback to localhost
            app_url = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{settings.PORT}")
            logger.info(f"Keep-alive pinging {app_url}/health...")
            async with httpx.AsyncClient() as client:
                await client.get(f"{app_url}/health", timeout=10.0)
        except Exception as e:
            logger.error(f"Keep-alive ping failed: {e}")

@app.on_event("startup")
async def startup_event():
    """
    Startup event for the FastAPI application.
    """
    logger.info("Starting up AI Chatbot...")
    await db.connect_to_storage()
    asyncio.create_task(keep_alive())

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
