"""
tests/test_public_preview.py
-------------------------------
GET /api/public/preview needs no login, so the card it builds must carry
catalog facts only. preview_card() is pure, so (per this project's
DB-free testing convention) it's tested on an unsaved Scholarship.

Run with:
    cd backend
    pytest tests/test_public_preview.py
"""

from datetime import date
from decimal import Decimal

from app.models import Scholarship
from app.routes.public import preview_card


def make(**overrides):
    fields = dict(
        id=7,
        title="Rivera Family STEM Scholarship",
        organization="Rivera Community Foundation",
        award_amount=Decimal("5000.00"),
        deadline=date(2027, 3, 15),
        grade_levels=["12"],
        states=["TX"],
        demographics=[],
        interests=["stem", "robotics", "math", "engineering"],
        renewable=True,
        num_awards=4,
        source_url="https://riverafoundation.org/stem",
        source_name="manual_seed",
        status="active",
    )
    fields.update(overrides)
    return Scholarship(**fields)


def test_card_has_only_public_catalog_fields():
    card = preview_card(make())
    assert set(card) == {
        "id", "title", "organization", "amount", "deadline", "grade_levels",
        "states", "demographics", "interests", "renewable", "num_awards",
    }
    assert card["amount"] == 5000.0
    assert card["deadline"] == "2027-03-15"
    assert card["interests"] == ["stem", "robotics", "math"]  # capped at 3 for the card


def test_rolling_and_missing_values_are_safe():
    card = preview_card(make(deadline=None, grade_levels=None, states=None, interests=None, renewable=None))
    assert card["deadline"] is None
    assert card["grade_levels"] == [] and card["states"] == [] and card["interests"] == []
    assert card["renewable"] is False
