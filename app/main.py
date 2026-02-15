import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.events import router as events_router
from app.api.metrics import router as metrics_router
from app.api.seed import router as seed_router
from app.db.session import init_db
from app.geo.mappings import validate_no_duplicate_codes
from app.scheduler.jobs import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_static_dir = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Social Listening System")
    validate_no_duplicate_codes()
    logger.info("Country code validation passed")

    await init_db()
    logger.info("Database initialized")

    scheduler = start_scheduler()

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


app = FastAPI(
    title="Social Listening System",
    description="Overseas Social Listening System - Event Detection & Trend Analysis",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(events_router)
app.include_router(metrics_router)
app.include_router(seed_router)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/")
async def dashboard():
    return FileResponse(os.path.join(_static_dir, "dashboard.html"))


@app.get("/health")
async def health():
    return {"status": "ok"}
