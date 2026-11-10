"""
scraper/questions_backfill.py
--------------------------------
Copies each scholarship's application questions from its official page
into Scholarship.questions, so students can answer them in the app.

  python -m scraper.questions_backfill                  # dry run: counts only
  python -m scraper.questions_backfill --apply          # write them
  python -m scraper.questions_backfill --apply --all    # redo rows that already have questions

Prints a summary, plus any essay-required listing where no essay question
could be found (those need a look by hand).
"""

import argparse
import logging
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from app.services import questions as Q
from scraper.daily_discovery import _visible_text
from scraper.link_checker import REQUEST_TIMEOUT_SECONDS, USER_AGENT

logger = logging.getLogger(__name__)


def fetch_questions(url: str, essay_required) -> list[dict] | None:
    """The questions on one official page, or None if it couldn't be read."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    html = resp.content.decode("utf-8", errors="replace")  # portals are UTF-8 but do not always say so
    return Q.build(html, _visible_text(html), essay_required)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--all", action="store_true", help="also redo rows that already have questions")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    from app import create_app
    from app.extensions import db
    from app.models import Scholarship

    app = create_app()
    with app.app_context():
        query = Scholarship.query.filter(Scholarship.is_active.is_(True), Scholarship.source_url.isnot(None))
        if not args.all:
            query = query.filter(Scholarship.questions.is_(None))
        rows = query.all()
        jobs = [(r.id, r.source_url, r.essay_required) for r in rows]
        # Release the connection while pages are fetched (hosted Postgres
        # drops idle ones).
        db.session.rollback()
        db.session.close()
        db.engine.dispose()

        def work(job):
            sid, url, essay = job
            time.sleep(0.2)
            return sid, essay, fetch_questions(url, essay)

        with ThreadPoolExecutor(args.workers) as ex:
            results = list(ex.map(work, jobs))

        counts = {"pages": len(results), "unreadable": 0, "with_questions": 0, "questions": 0}
        missing_essay = []
        for sid, essay, qs in results:
            if qs is None:
                counts["unreadable"] += 1
                continue
            counts["questions"] += len(qs)
            counts["with_questions"] += bool(qs)
            if essay and not any(q["kind"] == "written" for q in qs):
                missing_essay.append(sid)
            if args.apply:
                row = db.session.get(Scholarship, sid)
                row.questions = qs
        if args.apply:
            db.session.commit()
        print(
            f"{counts['pages']} pages, {counts['with_questions']} with questions "
            f"({counts['questions']} total), {counts['unreadable']} unreadable"
            + ("" if args.apply else " -- dry run, nothing written")
        )
        if missing_essay:
            print(f"essay required but no essay question found: {missing_essay}")


if __name__ == "__main__":
    main()
