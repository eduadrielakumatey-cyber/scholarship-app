"""
tests/test_hosted.py
-----------------------
Scholarships posted on ScholarMatch and the applications students submit to
them in the app. The checks are pure, so (per this project's DB-free testing
convention) they run on plain objects.

Run with:
    cd backend
    pytest tests/test_hosted.py
"""

from datetime import date, timedelta
from types import SimpleNamespace

from app.services.hosted import hash_token, new_review_token, validate_application, validate_listing

TODAY = date(2026, 11, 9)


def listing(**over):
    data = {
        "title": "Waldorf Hardware Trades Scholarship",
        "organization": "Waldorf Hardware",
        "description": "For Charles County seniors heading into a trade program. One $1,000 award paid to the school.",
        "essay_prompt": "Tell us what trade you want to learn and why.",
        "sponsor_name": "Pat Lee",
        "sponsor_email": "Pat@WaldorfHardware.com",
        "amount": 1000,
        "num_awards": 1,
        "deadline": "2027-03-01",
        "grade_levels": ["12"],
        "agree": True,
    }
    data.update(over)
    return data


def test_good_listing_passes_and_defaults_to_maryland():
    fields, errors = validate_listing(listing(), TODAY)
    assert errors == []
    assert fields["states"] == ["MD"]
    assert fields["sponsor_email"] == "pat@waldorfhardware.com"


def test_listing_rejects_bad_fields():
    _, errors = validate_listing(listing(amount=5, sponsor_email="nope", deadline="2026-11-10", agree=False), TODAY)
    joined = " | ".join(errors)
    assert "Award amount" in joined
    assert "valid email" in joined
    assert "at least a week" in joined
    assert "pay winners directly" in joined


def test_listing_rejects_far_deadline_and_unknown_grade():
    _, errors = validate_listing(listing(deadline="2029-01-01", grade_levels=["9"]), TODAY)
    assert any("15 months" in e for e in errors)
    assert any("who can apply" in e for e in errors)


def hosted(**over):
    s = dict(hosted=True, is_active=True, deadline=TODAY + timedelta(days=30), essay_prompt="Why?")
    s.update(over)
    return SimpleNamespace(**s)


def app_data(**over):
    data = {
        "full_name": "Jordan Smith",
        "email": "jordan@example.com",
        "school": "North Point High",
        "essay": " ".join(["word"] * 40),
        "share_consent": True,
    }
    data.update(over)
    return data


def test_good_application_passes():
    fields, errors = validate_application(app_data(), hosted(), TODAY)
    assert errors == []
    assert fields["email"] == "jordan@example.com"


def test_application_needs_consent_email_and_essay():
    _, errors = validate_application(app_data(share_consent=False, email="x", essay="too short"), hosted(), TODAY)
    joined = " | ".join(errors)
    assert "share your application" in joined
    assert "valid email" in joined
    assert "at least 25 words" in joined


def test_no_essay_needed_when_there_is_no_prompt():
    _, errors = validate_application(app_data(essay=""), hosted(essay_prompt=None), TODAY)
    assert errors == []


def test_cannot_apply_in_app_to_outside_closed_or_unapproved_scholarships():
    assert validate_application(app_data(), hosted(hosted=False), TODAY)[1]
    assert validate_application(app_data(), hosted(is_active=False), TODAY)[1]
    assert validate_application(app_data(), hosted(deadline=TODAY - timedelta(days=1)), TODAY)[1]


def test_review_tokens_are_random_and_only_hashes_are_compared():
    a, b = new_review_token(), new_review_token()
    assert a != b and len(a) >= 30
    assert hash_token(a) == hash_token(a) != hash_token(b)
    assert len(hash_token(a)) == 64
