"""evo-platform FastAPI application entrypoint.

Run with:
    uvicorn evo_platform.api.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="evo-platform",
    description="Universal AI Capability Platform - Agent Execution API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(agent_router, prefix="/v1", tags=["agents"])


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "evo-platform"}
