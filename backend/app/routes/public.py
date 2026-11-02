"""
app/routes/public.py
-----------------------
  GET /api/public/preview -> what the signed-out homepage shows: live
  counts plus a handful of real, open scholarships for the demo deck and
  the "due soon" list.

No login required, so it returns only catalog facts (title, amount,
deadline, who it's for) -- never anything about users. Only rows whose
link was verified (status "active") are showcased, so a visitor's first
look is never a dead link.
"""

from datetime import date

from flask import Blueprint, jsonify
from sqlalchemy import func

from app.models import Scholarship
from app.services.matching import _active_not_expired_query

public_bp = Blueprint("public", __name__, url_prefix="/api/public")

DEMO_CARDS = 6
DUE_SOON = 5


def preview_card(s: Scholarship) -> dict:
    return {
        "id": s.id,
        "title": s.title,
        "organization": s.organization,
        "amount": float(s.award_amount or 0),
        "deadline": s.deadline.isoformat() if s.deadline else None,
        "grade_levels": s.grade_levels or [],
        "states": s.states or [],
        "demographics": s.demographics or [],
        "interests": (s.interests or [])[:3],
        "renewable": bool(s.renewable),
        "num_awards": s.num_awards,
    }


@public_bp.get("/preview")
def preview():
    today = date.today()
    live = _active_not_expired_query(today)
    verified = live.filter(Scholarship.status == "active", Scholarship.award_amount > 0)

    # Demo deck: the biggest verified awards, so the first swipe is worth it.
    demo = verified.order_by(Scholarship.award_amount.desc(), Scholarship.id).limit(DEMO_CARDS).all()
    due_soon = (
        verified.filter(Scholarship.deadline.isnot(None))
        .order_by(Scholarship.deadline, Scholarship.id)
        .limit(DUE_SOON)
        .all()
    )
    total_value = live.with_entities(func.coalesce(func.sum(Scholarship.award_amount), 0)).scalar()

    return jsonify({
        "live_count": live.count(),
        "rolling_count": live.filter(Scholarship.deadline.is_(None)).count(),
        "total_value": float(total_value or 0),
        "demo_cards": [preview_card(s) for s in demo],
        "due_soon": [preview_card(s) for s in due_soon],
    })
