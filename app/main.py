import asyncio
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

_IS_VERCEL = bool(os.environ.get("VERCEL"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_static_dir = os.path.join(os.path.dirname(__file__), "static")


async def _auto_seed_background():
    """Check if DB is empty and auto-seed in background (non-blocking)."""
    try:
        from sqlalchemy import text
        from app.db.session import async_session_factory
        async with async_session_factory() as session:
            row = await session.execute(text("SELECT COUNT(*) FROM documents"))
            doc_count = row.scalar() or 0
        if doc_count == 0:
            logger.info("Database is empty, auto-seeding Reddit data in background...")
            from app.api.seed import seed_reddit_data
            async with async_session_factory() as session:
                await seed_reddit_data(session)
            logger.info("Auto-seed completed")
        else:
            logger.info("Database already has %d docs, skipping auto-seed", doc_count)
    except Exception:
        logger.exception("Auto-seed failed, dashboard will be empty until manual seed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Social Listening System")
    validate_no_duplicate_codes()
    logger.info("Country code validation passed")

    await init_db()
    logger.info("Database initialized")

    # Launch auto-seed as background task (non-blocking, server starts immediately)
    seed_task = None
    if not _IS_VERCEL:
        seed_task = asyncio.create_task(_auto_seed_background())

    # Skip scheduler on Vercel (serverless, no background process, no scikit-learn)
    scheduler = None
    if not _IS_VERCEL:
        from app.scheduler.jobs import start_scheduler
        scheduler = start_scheduler()

    yield

    # Shutdown
    if seed_task and not seed_task.done():
        seed_task.cancel()
    if scheduler:
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
