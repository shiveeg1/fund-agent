"""
scheduler.py — APScheduler cron definitions for the SIP Portfolio workflow.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import load_config
from main import run_workflow

logger = logging.getLogger(__name__)


def scheduled_job() -> None:
    """Entry point called by APScheduler."""
    logger.info("Scheduled job triggered.")
    config = load_config()
    try:
        run_workflow(config)
    except Exception:
        logger.exception("Scheduled workflow run failed.")
        raise


def build_scheduler() -> BlockingScheduler:
    config = load_config()
    scheduler = BlockingScheduler(timezone=config.timezone)
    scheduler.add_job(
        scheduled_job,
        trigger=CronTrigger(
            hour=config.run_hour,
            minute=config.run_minute,
            timezone=config.timezone,
        ),
        id="sip_portfolio_workflow",
        name="SIP Portfolio Daily Workflow",
        misfire_grace_time=300,
        coalesce=True,
    )
    logger.info(
        "Scheduler configured: daily at %02d:%02d %s",
        config.run_hour,
        config.run_minute,
        config.timezone,
    )
    return scheduler


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    scheduler = build_scheduler()
    logger.info("Starting scheduler. Press Ctrl+C to exit.")
    scheduler.start()
