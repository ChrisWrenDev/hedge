from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.modules.options_data.models import Base
from app.modules.data_sources.router import router as data_sources_router
from app.modules.options_data.router import router as options_router
from app.modules.ingestion.router import router as ingestion_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Hedge API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_sources_router, prefix="/api")
app.include_router(options_router, prefix="/api")
app.include_router(ingestion_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
