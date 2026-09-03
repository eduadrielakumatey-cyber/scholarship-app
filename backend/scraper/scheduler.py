"""
scraper/scheduler.py
-----------------------
Option A for running the scraper "every day at 5am": a small always-on
process that sleeps and wakes the scraper up on a cron-like schedule using
APScheduler. Use this if you're deploying to a server/VM/container that
stays running 24/7 (e.g. a small Docker container, an EC2 box, a Render
"Background Worker").

Run with:
    python -m scraper.scheduler

This process does nothing except wait and trigger scraper/run_scraper.py's
run() function once a day -- it is NOT the Flask API server. Run it as a
separate process/container from the web app (see docker-compose.yml's
`scraper` service).

Option B (no always-on process needed): use your platform's own scheduler
to invoke `python -m scraper.run_scraper` directly once a day, e.g.:
  - GitHub Actions scheduled workflow (see deployment/github-actions-scraper.yml)
  - Render / Railway / Heroku "Scheduler" / "Cron Job" add-ons
  - A plain Linux crontab entry if you're on your own VM:
        0 5 * * * cd /path/to/backend && /path/to/venv/bin/python -m scraper.run_scraper
  - AWS EventBridge Schedule -> Lambda or ECS Task

Option B is generally simpler and cheaper (no idle process burning
compute 23 hours and 59 minutes a day), so it's the recommended default --
this file exists for the cases where an in-app scheduler is more
convenient.
"""

import logging
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from scraper.run_scraper import run

logger = logging.getLogger("scraper.scheduler")
logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")


def scheduled_job():
    logger.info("Triggering scheduled scrape run")
    try:
        run()
    except Exception:
        logger.exception("Scheduled scrape run raised an unhandled exception")


def main():
    scheduler = BlockingScheduler(timezone="America/New_York")
    # Runs every day at 05:00 in the timezone above. Change `hour`/`minute`
    # or `timezone` to fit your users -- most of your users are US-based
    # high schoolers, so America/New_York is a reasonable default; switch
    # to their local timezone if you target a specific region.
    scheduler.add_job(scheduled_job, CronTrigger(hour=5, minute=0))
    logger.info("Scheduler started. Waiting for the next 5:00 AM trigger...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
