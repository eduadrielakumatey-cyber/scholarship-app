"""
validate_and_insert_batch.py
--------------------------------
The "be aggressive about discovery, conservative about insertion" gate
for discover_batch_2026_09.py. For every candidate:

  1. Skip it if a scholarship with the same (normalized title, organization)
     already exists in the database -- dedup against existing rows.
  2. Skip duplicates WITHIN the candidate batch itself.
  3. Check its source_url with scraper.link_checker.check_url (the exact
     same function the recurring freshness job uses, so a candidate is
     held to the same bar as an existing row).
  4. Only insert candidates whose check comes back "active". Anything
     "needs_review" or "unavailable" is rejected and logged with the
     reason -- never inserted blind.

Inserted rows get source_name="verified_batch_2026_09", a slugified
external_id, status="active", last_verified_at=now, is_active=True,
is_recurring_program=True (every candidate in this batch is a
well-established recurring program, not a one-time award).

Run with:
    python validate_and_insert_batch.py            # validate + insert
    python validate_and_insert_batch.py --dry-run   # validate only, insert nothing
"""

from __future__ import annotations

import argparse
import logging
import re
import time
from datetime import date, datetime

from app import create_app
from app.extensions import db
from app.models import Scholarship
from discover_batch_2026_09 import CANDIDATES
from scraper.dedupe import _normalize_url
from scraper.link_checker import REQUEST_DELAY_SECONDS, check_url

logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validate_and_insert_batch")

SOURCE_NAME = "verified_batch_2026_09"


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _existing_keys() -> set[tuple[str, str]]:
    keys = set()
    for s in Scholarship.query.with_entities(Scholarship.title, Scholarship.organization).all():
        keys.add((_normalize(s.title), _normalize(s.organization)))
    return keys


def _existing_urls() -> set[str]:
    urls = set()
    for s in Scholarship.query.with_entities(Scholarship.source_url).all():
        norm = _normalize_url(s.source_url)
        if norm:
            urls.add(norm)
    return urls


def run(dry_run: bool = False) -> dict:
    app = create_app("development")
    with app.app_context():
        totals = {
            "candidates": len(CANDIDATES),
            "duplicate_existing": 0,
            "duplicate_in_batch": 0,
            "rejected_unavailable": 0,
            "rejected_needs_review": 0,
            "inserted": 0,
        }

        existing_keys = _existing_keys()
        existing_urls = _existing_urls()
        seen_in_batch: set[tuple[str, str]] = set()
        seen_urls_in_batch: set[str] = set()

        for item in CANDIDATES:
            key = (_normalize(item["title"]), _normalize(item["organization"]))
            url_key = _normalize_url(item.get("source_url"))

            # Same official URL as an existing row is treated as the same
            # opportunity even if the title text differs slightly (e.g. an
            # org's single scholarships page covering more than one named
            # award) -- see scraper/dedupe.py, which caught exactly this
            # for three candidates in this batch's first run.
            if key in existing_keys or (url_key and url_key in existing_urls):
                logger.info("SKIP (already in DB): %r / %r", item["title"], item["organization"])
                totals["duplicate_existing"] += 1
                continue
            if key in seen_in_batch or (url_key and url_key in seen_urls_in_batch):
                logger.info("SKIP (duplicate within batch): %r", item["title"])
                totals["duplicate_in_batch"] += 1
                continue
            seen_in_batch.add(key)
            if url_key:
                seen_urls_in_batch.add(url_key)

            status, detail = check_url(item["source_url"])
            time.sleep(REQUEST_DELAY_SECONDS)

            if status == "unavailable":
                logger.warning("REJECT (unavailable): %r -> %s", item["title"], detail)
                totals["rejected_unavailable"] += 1
                continue
            if status == "needs_review":
                logger.warning("REJECT (needs_review, not auto-inserted): %r -> %s", item["title"], detail)
                totals["rejected_needs_review"] += 1
                continue

            logger.info("ACCEPT: %r -> %s", item["title"], detail)
            totals["inserted"] += 1

            if dry_run:
                continue

            deadline = None
            if item.get("deadline"):
                deadline = datetime.strptime(item["deadline"], "%Y-%m-%d").date()

            db.session.add(
                Scholarship(
                    title=item["title"],
                    organization=item.get("organization"),
                    description=item.get("description"),
                    award_amount=item.get("amount", 0),
                    award_frequency=item.get("award_frequency", "unknown"),
                    renewable=item.get("renewable"),
                    renewal_years=item.get("renewal_years"),
                    deadline=deadline,
                    min_gpa=item.get("min_gpa"),
                    grade_levels=item.get("grade_levels") or [],
                    states=item.get("states") or [],
                    demographics=item.get("demographics") or [],
                    majors=item.get("majors") or [],
                    interests=item.get("interests") or [],
                    estimated_hours_to_apply=item.get("estimated_hours_to_apply", 2.0),
                    estimated_applicant_pool=item.get("estimated_applicant_pool", 1000),
                    num_awards=item.get("num_awards", 1),
                    source_name=SOURCE_NAME,
                    source_url=item["source_url"],
                    external_id=_slug(item["title"]),
                    is_active=True,
                    status="active",
                    last_verified_at=datetime.utcnow(),
                    is_recurring_program=True,
                )
            )

        if not dry_run:
            db.session.commit()

        logger.info("Batch complete: %s", totals)
        return totals


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
