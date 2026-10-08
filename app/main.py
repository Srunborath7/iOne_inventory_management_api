from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.core.config import settings
from app.core.database import close_db, init_db, ping_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure upload directory exists
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Inventory Management API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware configured for development and production (Render/Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# Serve uploaded static media from configurable upload directory
app.mount(
    "/uploads",
    StaticFiles(directory=settings.upload_dir, check_dir=False),
    name="uploads",
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Inventory Management API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/healthz", tags=["Health"])
async def health_check():
    """Health check endpoint for Render zero-downtime deploys and monitoring."""
    db_ok = await ping_db()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "environment": settings.environment,
    }
