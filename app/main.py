from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Inventory Management API",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "message": "Inventory Management API"
    }