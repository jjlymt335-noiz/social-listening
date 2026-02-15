import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync scheduler callback."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _run_short_term():
    """Run the short-term engine synchronously (called by APScheduler)."""
    from app.db.session import async_session_factory
    from app.engine.short_term import run_short_term_engine

    logger.info("Starting short-term engine")
    try:
        async def _task():
            async with async_session_factory() as session:
                await run_short_term_engine(session)
        _run_async(_task())
        logger.info("Short-term engine completed")
    except Exception:
        logger.exception("Short-term engine failed")


def _run_long_term():
    """Run the long-term engine synchronously (called by APScheduler)."""
    from app.db.session import async_session_factory
    from app.engine.long_term import run_long_term_engine

    logger.info("Starting long-term engine")
    try:
        async def _task():
            async with async_session_factory() as session:
                await run_long_term_engine(session)
        _run_async(_task())
        logger.info("Long-term engine completed")
    except Exception:
        logger.exception("Long-term engine failed")


def start_scheduler() -> BackgroundScheduler:
    """Create and start the APScheduler with engine jobs."""
    scheduler = BackgroundScheduler(timezone="UTC")

    scheduler.add_job(
        _run_short_term, "interval", minutes=settings.SCAN_INTERVAL_MINUTES,
        id="short_term_engine", replace_existing=True,
    )
    scheduler.add_job(
        _run_long_term, "cron", hour=0, minute=0,
        id="long_term_engine", replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started: short-term every %d min, long-term daily 00:00 UTC",
        settings.SCAN_INTERVAL_MINUTES,
    )
    return scheduler
