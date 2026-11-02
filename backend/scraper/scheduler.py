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

FRESHNESS JOB -- separate from the daily discovery run above, this also
schedules a WEEKLY pass of scraper/link_checker.py (re-verifies every
row's URL, flags/deactivates dead ones) and scraper/dedupe.py (flags/
deactivates duplicate rows). Weekly, not daily: it's real-world traffic
against dozens of third-party domains, and scholarship links don't
typically go dead or duplicate within a single day, so daily would just
be unnecessary load for no added benefit. If you're using Option B
instead of this file, add the equivalent as its own cron line:
    0 6 * * 0 cd /path/to/backend && /path/to/venv/bin/python -m scraper.link_checker
    15 6 * * 0 cd /path/to/backend && /path/to/venv/bin/python -m scraper.dedupe --deactivate
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


def scheduled_freshness_job():
    """Weekly link-health + duplicate sweep. Runs link_checker fully
    (only --only-stale-days would skip recently-checked rows, but a
    weekly cadence over ~300-2000 rows is already cheap enough not to
    need that), then dedupe with --deactivate so newly-discovered
    duplicates don't sit around waiting for a manual run."""
    logger.info("Triggering weekly link-health + dedupe sweep")
    try:
        from scraper.link_checker import run as run_link_checker
        run_link_checker()
    except Exception:
        logger.exception("Weekly link check raised an unhandled exception")
    try:
        from scraper.dedupe import run as run_dedupe
        run_dedupe(deactivate=True)
    except Exception:
        logger.exception("Weekly dedupe pass raised an unhandled exception")


def main():
    scheduler = BlockingScheduler(timezone="America/New_York")
    # Runs every day at 05:00 in the timezone above. Change `hour`/`minute`
    # or `timezone` to fit your users -- most of your users are US-based
    # high schoolers, so America/New_York is a reasonable default; switch
    # to their local timezone if you target a specific region.
    scheduler.add_job(scheduled_job, CronTrigger(hour=5, minute=0))
    # Weekly freshness sweep, offset an hour later so it never overlaps
    # the daily discovery run above.
    scheduler.add_job(scheduled_freshness_job, CronTrigger(day_of_week="sun", hour=6, minute=0))
    logger.info("Scheduler started. Waiting for the next scheduled trigger...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
