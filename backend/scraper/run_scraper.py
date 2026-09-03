"""
scraper/run_scraper.py
-------------------------
This is the script that actually does "look for new scholarships and
update the database." It is meant to be triggered once per run by an
external scheduler (cron, GitHub Actions, a cloud Scheduler job -- see
scraper/scheduler.py and deployment/ for options), NOT by leaving a
terminal open.

What it does:
  1. Iterates every registered source (see SOURCES below)
  2. Calls source.fetch() to get a normalized list of scholarship dicts
  3. Upserts each one into the `scholarships` table, matched on
     (source_name, external_id) so re-running never creates duplicates
  4. Marks rows from a source as inactive if that source no longer lists
     them (e.g. the scholarship's deadline passed and it dropped off the
     provider's feed) -- handled per-source so one failing source doesn't
     deactivate another source's listings.
  5. Logs a summary (created / updated / deactivated / errors) so you can
     monitor whether the job is actually finding anything.

Run manually with:
    python -m scraper.run_scraper
"""

import logging
import os
import sys
from datetime import datetime

from app import create_app
from app.extensions import db
from app.models import Scholarship
from scraper.sources.example_api_source import ExampleApiSource
from scraper.sources.example_html_source import ExampleHtmlSource

logging.basicConfig(
    level=os.environ.get("SCRAPER_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("scraper")

# Register every source you want the nightly job to pull from here.
# Add a new source by importing its class above and adding an instance
# to this list -- no other code needs to change.
SOURCES = [
    ExampleApiSource(),
    ExampleHtmlSource(),
]


def upsert_scholarship(source_name: str, item: dict) -> str:
    """Returns 'created' or 'updated'."""
    existing = Scholarship.query.filter_by(
        source_name=source_name, external_id=item["external_id"]
    ).first()

    deadline = None
    if item.get("deadline"):
        try:
            deadline = datetime.strptime(item["deadline"], "%Y-%m-%d").date()
        except ValueError:
            logger.warning("Could not parse deadline %r for %r", item.get("deadline"), item.get("title"))

    fields = dict(
        title=item["title"],
        organization=item.get("organization"),
        description=item.get("description"),
        amount=item.get("amount", 0),
        deadline=deadline,
        min_gpa=item.get("min_gpa"),
        grade_levels=item.get("grade_levels") or [],
        states=item.get("states") or [],
        demographics=item.get("demographics") or [],
        majors=item.get("majors") or [],
        interests=item.get("interests") or [],
        estimated_hours_to_apply=item.get("estimated_hours_to_apply", 2.0),
        estimated_applicant_pool=item.get("estimated_applicant_pool", 500),
        num_awards=item.get("num_awards", 1),
        source_url=item.get("source_url"),
        is_active=True,
    )

    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        return "updated"
    else:
        db.session.add(
            Scholarship(source_name=source_name, external_id=item["external_id"], **fields)
        )
        return "created"


def deactivate_missing(source_name: str, seen_external_ids: set[str]) -> int:
    """
    Any scholarship previously stored from this source that did NOT show
    up in this run gets marked inactive (soft delete) so it stops being
    shown to users, without losing historical data (e.g. past interactions
    referencing it).
    """
    stale = Scholarship.query.filter(
        Scholarship.source_name == source_name,
        Scholarship.is_active.is_(True),
        ~Scholarship.external_id.in_(seen_external_ids) if seen_external_ids else True,
    ).all()
    for row in stale:
        row.is_active = False
    return len(stale)


def run():
    app = create_app(os.environ.get("FLASK_ENV", "production"))
    with app.app_context():
        totals = {"created": 0, "updated": 0, "deactivated": 0, "source_errors": 0}

        for source in SOURCES:
            logger.info("Running source: %s", source.name)
            try:
                items = source.fetch()
            except Exception:
                logger.exception("Source %s failed -- skipping it this run", source.name)
                totals["source_errors"] += 1
                continue

            seen_ids = set()
            for item in items:
                try:
                    result = upsert_scholarship(source.name, item)
                    totals[result] += 1
                    seen_ids.add(item["external_id"])
                except Exception:
                    logger.exception("Failed to upsert item %r from %s", item.get("title"), source.name)

            if items:  # only deactivate-missing if the source returned anything at all,
                       # so a totally-failed fetch doesn't wipe out a source's listings
                deactivated = deactivate_missing(source.name, seen_ids)
                totals["deactivated"] += deactivated

            db.session.commit()
            logger.info("Finished source: %s (%d items)", source.name, len(items))

        logger.info("Scrape run complete: %s", totals)
        return totals


if __name__ == "__main__":
    result = run()
    # Non-zero exit if every source errored, so a cron/CI runner can flag
    # the job as failed instead of silently "succeeding" with zero data.
    if result["source_errors"] >= len(SOURCES) and len(SOURCES) > 0:
        sys.exit(1)
