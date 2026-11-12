"""
app/services/stats.py
------------------------
Builds the payload for the "Stats for Idiots" page: a small, honest
summary of a user's OWN activity, computed entirely from their own
Interaction rows and the Scholarship rows those interactions reference.

Nothing here is invented. "currently_matching" reuses the exact same
eligibility/match-quality check the swipe deck itself uses (via
matching.get_match_counts), so it can never disagree with what the user
sees in Discover. Everything else is a direct count, sum, or average
over real rows -- there is no synthetic/placeholder data path, and a
user with no history gets honest zeros/nulls, not fabricated numbers.

The frontend (src/pages/Stats.jsx) is responsible for turning these
numbers into plain-English sentences -- this module only computes them.
"""

from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models import Interaction, Scholarship
from app.services.matching import get_match_counts

# Application-tracker statuses (see Interaction.app_status) that count as
# "started working on it" vs. "already sent off."
_STARTED_STATUSES = {"planning", "in_progress", "submitted", "won", "declined"}
_SUBMITTED_STATUSES = {"submitted", "won", "declined"}

# Buckets for "most of your saved scholarships are worth between $X-$Y" --
# a plain-English modal range, not a statistical distribution.
_AMOUNT_BUCKETS = [(0, 1000), (1000, 5000), (5000, 10000), (10000, None)]


def _interaction_rows(user_id: int):
    return (
        db.session.query(
            Interaction.action,
            Interaction.app_status,
            Scholarship.award_amount,
            Scholarship.amount_varies,
            Scholarship.title,
            Scholarship.interests,
            Scholarship.deadline,
        )
        .join(Scholarship, Scholarship.id == Interaction.scholarship_id)
        .filter(Interaction.user_id == user_id)
        .all()
    )


def _amount_bucket(amount: float) -> tuple[float, float | None]:
    for lo, hi in _AMOUNT_BUCKETS:
        if amount >= lo and (hi is None or amount < hi):
            return (lo, hi)
    return _AMOUNT_BUCKETS[-1]


def build_stats(user) -> dict:
    rows = _interaction_rows(user.id)
    today = date.today()

    saved_rows = [r for r in rows if r.action == "save"]
    viewed_count = len(rows)
    saved_count = len(saved_rows)
    skipped_count = sum(1 for r in rows if r.action == "pass")

    save_rate_percent = round(100 * saved_count / viewed_count, 1) if viewed_count else None

    match_counts = get_match_counts(user)

    # "Amount varies" awards have no dollar figure, so they're left out of
    # the money totals instead of counting as $0.
    saved_amounts = [float(r.award_amount or 0) for r in saved_rows if not r.amount_varies]
    total_saved_value = round(sum(saved_amounts), 2)
    average_saved_award = round(total_saved_value / len(saved_amounts), 2) if saved_amounts else None
    highest_row = max(saved_rows, key=lambda r: float(r.award_amount or 0), default=None)
    highest_saved = (
        {"title": highest_row.title, "amount": float(highest_row.award_amount or 0)}
        if highest_row
        else None
    )

    started = sum(1 for r in saved_rows if (r.app_status or "saved") in _STARTED_STATUSES)
    submitted = sum(1 for r in saved_rows if (r.app_status or "saved") in _SUBMITTED_STATUSES)
    potential_from_submitted = round(
        sum(float(r.award_amount or 0) for r in saved_rows if r.app_status == "submitted"), 2
    )

    upcoming_rows = sorted(
        (
            r
            for r in saved_rows
            if r.deadline and r.deadline >= today and (r.app_status or "saved") not in ("won", "declined")
        ),
        key=lambda r: r.deadline,
    )[:5]
    upcoming_deadlines = [
        {
            "title": r.title,
            "amount": float(r.award_amount or 0),
            "amount_varies": bool(r.amount_varies),
            "deadline": r.deadline.isoformat(),
            "days_left": (r.deadline - today).days,
        }
        for r in upcoming_rows
    ]

    tag_counts: dict[str, int] = {}
    for r in saved_rows:
        for tag in list(r.interests or []):
            tag = tag.strip().lower()
            if tag:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    top_saved_category = max(tag_counts, key=tag_counts.get) if tag_counts else None

    bucket_counts: dict[tuple, int] = {}
    for amount in saved_amounts:
        bucket = _amount_bucket(amount)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    top_bucket = max(bucket_counts, key=bucket_counts.get) if bucket_counts else None

    return {
        "activity": {
            "viewed": viewed_count,
            "saved": saved_count,
            "skipped": skipped_count,
            "save_rate_percent": save_rate_percent,
            "currently_matching": match_counts["eligible_count"],
            "strongly_matching": match_counts["strong_match_count"],
        },
        "money": {
            "total_saved_value": total_saved_value,
            "average_saved_award": average_saved_award,
            "highest_saved": highest_saved,
        },
        "applications": {
            "started": started,
            "submitted": submitted,
            "upcoming_deadlines": upcoming_deadlines,
            "potential_from_submitted": potential_from_submitted,
        },
        "insights": {
            "top_saved_category": top_saved_category,
            "typical_saved_range": (
                {"min": top_bucket[0], "max": top_bucket[1]} if top_bucket else None
            ),
        },
    }
