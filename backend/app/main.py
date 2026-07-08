from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import audit, chat, health, upload
from app.core.config import settings
from app.core.deps import init_graph, shutdown_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_graph()
    yield
    await shutdown_graph()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(audit.router)
