"""
scraper/link_checker.py
--------------------------
The dead-link-detection system called for in the scholarship-database
quality pass. Modular and conservative on purpose: it only ever flips a
row to `unavailable` (and is_active=False) when there's a real signal the
link is gone, and otherwise records `needs_review` rather than guessing.
It never inserts, deletes, or invents data -- it only updates
status/last_verified_at/is_active on rows that already exist.

Classification rules (see check_url()):
  - Network/DNS failure, timeout, or HTTP 404/410           -> unavailable
  - HTTP 2xx/3xx AND the page text contains a strong
    "this program has ended" signal                          -> unavailable
  - HTTP 2xx/3xx with no red flags                            -> active
  - Anything else (403s from bot-blocking, 5xx, redirect
    loops, ambiguous content, no source_url at all)           -> needs_review
    (403/5xx is common for sites that block scripted clients
    even when the page is perfectly live for a real browser --
    treating that as "dead" would produce false positives, so
    it's routed to a human/manual re-check instead.)

Usage:
    python -m scraper.link_checker                # check every scholarship
    python -m scraper.link_checker --limit 50      # check only the first 50
    python -m scraper.link_checker --only-stale-days 30
                                                    # only rows not verified
                                                    # in the last 30 days

Rate limiting: one request at a time with a short delay between them
(see REQUEST_DELAY_SECONDS) -- this hits dozens of different real-world
domains, not one site repeatedly, but a small delay plus a real
User-Agent and a short timeout keep it a well-behaved, not-hammering
client either way.
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timedelta

import requests

from app import create_app
from app.extensions import db
from app.models import Scholarship

logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scraper.link_checker")

REQUEST_DELAY_SECONDS = 0.4
REQUEST_TIMEOUT_SECONDS = 12
USER_AGENT = (
    "Mozilla/5.0 (compatible; ScholarMatchLinkChecker/1.0; "
    "+https://github.com/ -- verifies scholarship links are still live)"
)

# Strong, low-false-positive phrases only -- things a page says about
# ITSELF being over, not incidental uses of similar words elsewhere on
# the page (e.g. a nav link reading "past scholars" shouldn't trip this).
DEAD_PROGRAM_PHRASES = [
    "this scholarship is no longer",
    "this program has ended",
    "this program is no longer active",
    "no longer accepting applications",
    "the scholarship has been discontinued",
    "this award has been discontinued",
    "this contest has ended and is not currently accepting",
    "domain for sale",
    "this site can't be reached",
]


def check_url(url: str) -> tuple[str, str]:
    """Returns (status, detail). status is one of active/unavailable/needs_review."""
    if not url:
        return "needs_review", "no source_url on record"

    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(
            url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=True
        )
    except requests.exceptions.SSLError as exc:
        return "needs_review", f"SSL error: {exc}"
    except requests.exceptions.ConnectionError as exc:
        return "unavailable", f"connection failed (DNS/refused): {exc}"
    except requests.exceptions.Timeout:
        return "needs_review", "request timed out"
    except requests.exceptions.RequestException as exc:
        return "needs_review", f"request error: {exc}"

    if response.status_code in (404, 410):
        return "unavailable", f"HTTP {response.status_code}"

    if response.status_code == 403:
        # Very common for legitimate sites with bot protection (Cloudflare,
        # Akamai, etc.) -- a script getting blocked is not evidence the
        # scholarship is gone.
        return "needs_review", "HTTP 403 (likely bot-blocked, not necessarily dead)"

    if 500 <= response.status_code < 600:
        return "needs_review", f"HTTP {response.status_code} (server error, may be transient)"

    if not (200 <= response.status_code < 400):
        return "needs_review", f"unexpected HTTP {response.status_code}"

    text = (response.text or "").lower()[:200_000]  # cap -- don't scan huge pages fully
    for phrase in DEAD_PROGRAM_PHRASES:
        if phrase in text:
            return "unavailable", f"page text matched dead-program signal: {phrase!r}"

    return "active", f"HTTP {response.status_code}, no dead-program signal found"


def run(limit: int | None = None, only_stale_days: int | None = None) -> dict:
    app = create_app("development")
    with app.app_context():
        query = Scholarship.query.order_by(Scholarship.id)
        if only_stale_days is not None:
            cutoff = datetime.utcnow() - timedelta(days=only_stale_days)
            query = query.filter(
                db.or_(Scholarship.last_verified_at.is_(None), Scholarship.last_verified_at < cutoff)
            )
        if limit:
            query = query.limit(limit)
        rows = query.all()

        totals = {"active": 0, "unavailable": 0, "needs_review": 0, "checked": 0}
        for row in rows:
            status, detail = check_url(row.source_url)
            row.status = status
            row.last_verified_at = datetime.utcnow()
            if status == "unavailable":
                row.is_active = False
            totals[status] += 1
            totals["checked"] += 1
            logger.info("[%s] id=%s %r -> %s (%s)", totals["checked"], row.id, row.title, status, detail)
            db.session.commit()
            time.sleep(REQUEST_DELAY_SECONDS)

        logger.info("Link check complete: %s", totals)
        return totals


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--only-stale-days", type=int, default=None)
    args = parser.parse_args()
    run(limit=args.limit, only_stale_days=args.only_stale_days)
