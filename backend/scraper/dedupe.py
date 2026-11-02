"""
scraper/dedupe.py
--------------------
Duplicate detection for the scholarships table. The same scholarship
often shows up more than once when data comes from multiple seed
batches/sources (an aggregator and a manual entry, a re-scrape after a
title tweak, etc.) -- this finds likely duplicate PAIRS without deleting
anything automatically, since merging is a judgment call (which row has
the better description, the more complete metadata, etc.) that deserves
a human/manual look rather than an automatic keep-first-drop-rest rule.

Matches on, in order of confidence:
  1. Same normalized official URL (strip scheme/www/trailing slash) --
     the strongest signal: two rows pointing at the exact same page.
  2. Same normalized (title, organization) pair, allowing for minor
     punctuation/whitespace differences.
  3. Same normalized title alone with a similar organization (fuzzy
     match via difflib) -- catches near-duplicates like "XYZ Scholarship"
     vs "XYZ Scholarship Program".

Usage:
    python -m scraper.dedupe                 # report only
    python -m scraper.dedupe --deactivate     # also soft-delete (is_active=False)
                                               # the newer/lower-quality
                                               # row of each confirmed pair
"""

from __future__ import annotations

import argparse
import difflib
import re
from collections import defaultdict
from urllib.parse import urlparse

from app import create_app
from app.extensions import db
from app.models import Scholarship

TITLE_SIMILARITY_THRESHOLD = 0.85


def _normalize_text(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url.lower().strip())
    host = parsed.netloc.replace("www.", "")
    path = parsed.path.rstrip("/")
    return f"{host}{path}" if host else None


def _completeness_score(s: Scholarship) -> int:
    """More non-empty fields = 'better' row to keep when a pair is a duplicate."""
    fields = [s.description, s.source_url, s.deadline, s.min_gpa, s.organization]
    score = sum(1 for f in fields if f)
    score += len(s.grade_levels or []) + len(s.majors or []) + len(s.interests or [])
    return score


def find_duplicates() -> list[tuple[Scholarship, Scholarship, str]]:
    """Returns a list of (keep, drop, reason) tuples -- `drop` is the one
    with strictly lower completeness; ties keep the lower id (older/first-seeded)."""
    app = create_app("development")
    with app.app_context():
        rows = Scholarship.query.filter(Scholarship.is_active.is_(True)).all()

        pairs: list[tuple[Scholarship, Scholarship, str]] = []
        seen_pair_ids: set[frozenset] = set()

        def _record(a, b, reason):
            key = frozenset((a.id, b.id))
            if key in seen_pair_ids:
                return
            seen_pair_ids.add(key)
            if _completeness_score(a) >= _completeness_score(b):
                pairs.append((a, b, reason))
            else:
                pairs.append((b, a, reason))

        # --- 1. Same normalized URL ---
        by_url: dict[str, list[Scholarship]] = defaultdict(list)
        for s in rows:
            norm = _normalize_url(s.source_url)
            if norm:
                by_url[norm].append(s)
        for norm, group in by_url.items():
            if len(group) > 1:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        _record(group[i], group[j], f"same URL ({norm})")

        # --- 2. Same normalized (title, organization) ---
        by_title_org: dict[tuple[str, str], list[Scholarship]] = defaultdict(list)
        for s in rows:
            key = (_normalize_text(s.title), _normalize_text(s.organization))
            by_title_org[key].append(s)
        for key, group in by_title_org.items():
            if len(group) > 1:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        _record(group[i], group[j], f"same title+organization ({key[0]!r})")

        # --- 3. Fuzzy title match within the same organization ---
        by_org: dict[str, list[Scholarship]] = defaultdict(list)
        for s in rows:
            by_org[_normalize_text(s.organization)].append(s)
        for org, group in by_org.items():
            if not org or len(group) < 2:
                continue
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    a, b = group[i], group[j]
                    if a.id == b.id:
                        continue
                    ratio = difflib.SequenceMatcher(
                        None, _normalize_text(a.title), _normalize_text(b.title)
                    ).ratio()
                    if ratio >= TITLE_SIMILARITY_THRESHOLD:
                        _record(a, b, f"similar title within same org (ratio={ratio:.2f})")

        return pairs


def run(deactivate: bool = False) -> dict:
    pairs = find_duplicates()
    for keep, drop, reason in pairs:
        print(f"DUPLICATE: keep id={keep.id} {keep.title!r} | drop id={drop.id} {drop.title!r} -- {reason}")

    if deactivate and pairs:
        app = create_app("development")
        with app.app_context():
            drop_ids = {drop.id for _keep, drop, _reason in pairs}
            for row in Scholarship.query.filter(Scholarship.id.in_(drop_ids)).all():
                row.is_active = False
            db.session.commit()
            print(f"Deactivated {len(drop_ids)} duplicate rows.")

    return {"duplicate_pairs": len(pairs)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deactivate", action="store_true")
    args = parser.parse_args()
    run(deactivate=args.deactivate)
