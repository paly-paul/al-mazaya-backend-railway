"""
APScheduler tasks for Mazaya FM.
Schedules daily briefing generation at 08:00 Kuwait time.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

KUWAIT_TZ = "Asia/Kuwait"


async def _run_daily_briefing():
    """Called by scheduler at 08:00 Kuwait time."""
    from database import SessionLocal
    from agent.tools import handle_generate_briefing

    logger.info("Running scheduled daily briefing generation...")
    db = SessionLocal()
    try:
        result = handle_generate_briefing(db, {"period": "daily", "language": "en"})
        logger.info(f"Daily briefing generated: id={result.get('briefing_id')}")
    except Exception as e:
        logger.exception(f"Daily briefing generation failed: {e}")
    finally:
        db.close()


async def _run_weekly_briefing():
    """Called by scheduler at 09:00 Kuwait time on Mondays."""
    from database import SessionLocal
    from agent.tools import handle_generate_briefing

    logger.info("Running scheduled weekly briefing generation...")
    db = SessionLocal()
    try:
        result = handle_generate_briefing(db, {"period": "weekly", "language": "en"})
        logger.info(f"Weekly briefing generated: id={result.get('briefing_id')}")
    except Exception as e:
        logger.exception(f"Weekly briefing generation failed: {e}")
    finally:
        db.close()


def start_scheduler():
    """Register jobs and start the scheduler."""
    scheduler.add_job(
        _run_daily_briefing,
        trigger=CronTrigger(hour=8, minute=0, timezone=KUWAIT_TZ),
        id="daily_briefing",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        _run_weekly_briefing,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=0, timezone=KUWAIT_TZ),
        id="weekly_briefing",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Scheduler started: daily briefing at 08:00 Kuwait, weekly at 09:00 Kuwait (Monday)")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
