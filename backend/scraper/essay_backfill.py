"""
scraper/essay_backfill.py
-------------------------
Fills Scholarship.essay_required by reading each listing's official page.

Conservative on purpose: a card shows "Essay required" / "No essay" only
when the provider's own page says so. Anything unclear (page unreachable,
essay mentioned as optional, no mention at all) stays NULL and the card
shows no essay tag, rather than a guess.

  python -m scraper.essay_backfill            # dry run: prints what it would set
  python -m scraper.essay_backfill --apply    # writes the values
  python -m scraper.essay_backfill --apply --only-missing
"""

from __future__ import annotations

import argparse
import re
from concurrent.futures import ThreadPoolExecutor

import requests

from scraper.daily_discovery import REQUEST_TIMEOUT_SECONDS, USER_AGENT, _visible_text

# "No essay" only as a statement about this award -- not the plural
# "no essay scholarships", which is almost always a site's nav link.
NO_ESSAY = re.compile(
    r"\bno[- ]essays? (is |are )?(required|needed|necessary)\b"
    r"|\bno[- ]essay scholarship\b(?!s)"
    r"|\b(does|do) not require (an |a )?essays?\b"
    r"|\b(requires?|required|needs?|there (is|are)) no essays?\b"
    r"|\bessays? (is |are )?not required\b"
    r"|\bwithout (writing )?an essay\b"
)
OPTIONAL_ESSAY = re.compile(r"\boptional (essay|personal statement)\b|\b(essay|personal statement) (is )?optional\b")
_ESSAY_WORD = r"(essays?|personal statement|statement of (purpose|goals|intent)|writing prompt|short[- ]answer)"
_REQUIREMENT = r"(submit|required|requires|requirement|must|write|written|prompt|\d{2,4}[- ]words?|word (limit|count)|include)"
# An essay word counts only next to requirement language (either order,
# within ~60 characters), so a stray "read our essay" blog link doesn't.
ESSAY = re.compile(
    rf"\b{_ESSAY_WORD}\b.{{0,60}}\b{_REQUIREMENT}"
    rf"|\b{_REQUIREMENT}\b.{{0,60}}\b{_ESSAY_WORD}\b"
)


def classify(page_text: str, title: str = "") -> bool | None:
    """True = essay asked for, False = page says no essay, None = can't tell."""
    if re.search(r"\bessay (contest|competition|scholarship)\b", (title or "").lower()):
        return True
    text = re.sub(r"\s+", " ", (page_text or "").lower())
    if NO_ESSAY.search(text):
        return False
    if OPTIONAL_ESSAY.search(text):
        return None
    if ESSAY.search(text):
        return True
    return None


def _fetch_text(url: str) -> str | None:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException:
        return None
    if not 200 <= resp.status_code < 300 or "html" not in resp.headers.get("Content-Type", "html"):
        return None
    return _visible_text(resp.text)


def check(job: tuple[str, list[str]]) -> bool | None:
    """Reads the apply page first, then the info page; first clear answer wins."""
    title, urls = job
    for url in urls:
        text = _fetch_text(url)
        if text is None:
            continue
        verdict = classify(text, title)
        if verdict is not None:
            return verdict
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write results (default: dry run)")
    parser.add_argument("--only-missing", action="store_true", help="skip rows already checked")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    from app import create_app
    from app.extensions import db
    from app.models import Scholarship

    app = create_app()
    with app.app_context():
        query = Scholarship.query.filter_by(is_active=True)
        if args.only_missing:
            query = query.filter(Scholarship.essay_required.is_(None))
        rows = query.all()
        jobs = {
            s.id: (s.title, [u for u in dict.fromkeys([s.application_url, s.source_url]) if u])
            for s in rows
        }
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = dict(zip(jobs, pool.map(check, jobs.values())))

        counts = {True: 0, False: 0, None: 0}
        for s in rows:
            verdict = results[s.id]
            counts[verdict] += 1
            if args.apply and verdict is not None:
                s.essay_required = verdict
        if args.apply:
            db.session.commit()
        print(
            f"{len(rows)} checked: {counts[True]} essay required, {counts[False]} no essay, "
            f"{counts[None]} unclear{'' if args.apply else ' (dry run, nothing written)'}"
        )


if __name__ == "__main__":
    main()
