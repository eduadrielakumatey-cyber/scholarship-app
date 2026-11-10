"""
app/services/hosted.py
-------------------------
Pure checks for scholarships posted on ScholarMatch by sponsors and for the
applications students submit to them inside the app. Kept free of the
database so they can be tested without one.
"""

import hashlib
import re
import secrets
from datetime import date, datetime

from app.utils.validators import GRADE_LEVEL_CODES, US_STATE_CODES

EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,24}$")
MAX_DAYS_OUT = 450
MAX_ESSAY_CHARS = 8000
MIN_ESSAY_WORDS = 25


def new_review_token() -> str:
    return secrets.token_urlsafe(24)


def hash_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _text(data, key, lo, hi, errors, label, required=True):
    value = str(data.get(key) or "").strip()
    if not value and not required:
        return None
    if not (lo <= len(value) <= hi):
        errors.append(f"{label} must be {lo}-{hi} characters")
    return value


def validate_listing(data: dict, today: date | None = None) -> tuple[dict, list[str]]:
    """Checks a sponsor's new scholarship. Returns (clean_fields, errors)."""
    today = today or date.today()
    errors: list[str] = []
    f = {
        "title": _text(data, "title", 4, 160, errors, "Scholarship name"),
        "organization": _text(data, "organization", 2, 160, errors, "Sponsor or organization name"),
        "description": _text(data, "description", 40, 2000, errors, "Description"),
        "essay_prompt": _text(data, "essay_prompt", 10, 1000, errors, "Essay question", required=False),
        "sponsor_name": _text(data, "sponsor_name", 2, 160, errors, "Your name"),
    }

    email = str(data.get("sponsor_email") or "").strip()
    if not EMAIL.match(email):
        errors.append("Enter a valid email so we can reach you")
    f["sponsor_email"] = email.lower()

    amount = data.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not 50 <= amount <= 100_000:
        errors.append("Award amount must be between $50 and $100,000")
    f["award_amount"] = amount

    num = data.get("num_awards", 1)
    if isinstance(num, bool) or not isinstance(num, int) or not 1 <= num <= 100:
        errors.append("Number of awards must be 1-100")
    f["num_awards"] = num

    try:
        deadline = datetime.strptime(str(data.get("deadline") or ""), "%Y-%m-%d").date()
        days = (deadline - today).days
        if days < 7:
            errors.append("Deadline must be at least a week away")
        elif days > MAX_DAYS_OUT:
            errors.append("Deadline must be within about 15 months")
        f["deadline"] = deadline
    except ValueError:
        errors.append("Deadline must be a date")
        f["deadline"] = None

    grades = data.get("grade_levels") or []
    if not isinstance(grades, list) or not grades or any(g not in GRADE_LEVEL_CODES for g in grades):
        errors.append("Pick who can apply")
    f["grade_levels"] = grades

    states = data.get("states") if data.get("states") is not None else ["MD"]
    if not isinstance(states, list) or any(str(s).upper() not in US_STATE_CODES for s in states):
        errors.append("Unknown state")
        states = []
    f["states"] = [str(s).upper() for s in states]

    gpa = data.get("min_gpa")
    if gpa in ("", None):
        gpa = None
    elif isinstance(gpa, bool) or not isinstance(gpa, (int, float)) or not 0 < gpa <= 5:
        errors.append("Minimum GPA must be between 0 and 5")
    f["min_gpa"] = gpa

    if data.get("agree") is not True:
        errors.append("You must agree to pay winners directly and keep applicants' information private")
    return f, errors


def validate_application(data: dict, scholarship, today: date | None = None) -> tuple[dict, list[str]]:
    """Checks a student's in-app application. Returns (clean_fields, errors)."""
    today = today or date.today()
    errors: list[str] = []
    if not getattr(scholarship, "hosted", False):
        return {}, ["This scholarship is applied to on the provider's own website"]
    if not scholarship.is_active:
        return {}, ["This scholarship isn't accepting applications"]
    if scholarship.deadline and scholarship.deadline < today:
        return {}, ["The deadline for this scholarship has passed"]

    f = {
        "full_name": _text(data, "full_name", 2, 120, errors, "Your name"),
        "school": _text(data, "school", 2, 160, errors, "School", required=False),
    }
    email = str(data.get("email") or "").strip()
    if not EMAIL.match(email):
        errors.append("Enter a valid email so the sponsor can reach you if you win")
    f["email"] = email.lower()

    essay = str(data.get("essay") or "").strip()
    if scholarship.essay_prompt:
        if len(essay.split()) < MIN_ESSAY_WORDS:
            errors.append(f"Your essay needs at least {MIN_ESSAY_WORDS} words")
        if len(essay) > MAX_ESSAY_CHARS:
            errors.append("Your essay is too long")
    f["essay"] = essay or None

    if data.get("share_consent") is not True:
        errors.append("You must agree to share your application with the sponsor")
    return f, errors
