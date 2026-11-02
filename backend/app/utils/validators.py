"""
app/utils/validators.py
--------------------------
Tiny shared helpers for validating request payloads. Kept separate from the
route files so validation rules aren't duplicated if more than one endpoint
needs the same check.
"""

US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}


def is_valid_state(code: str | None) -> bool:
    return bool(code) and code.strip().upper() in US_STATE_CODES


# "12" = high school senior; the rest are college class years. Grades 9-11
# were dropped as a selectable audience -- product direction is that this
# app's users are mostly college students, plus HS seniors about to become
# college students, not younger high schoolers.
GRADE_LEVEL_CODES = {"12", "college_1", "college_2", "college_3", "college_4", "college_5plus"}


def is_valid_grade_level(value: str | None) -> bool:
    return value in GRADE_LEVEL_CODES


_MAX_INTEREST_LENGTH = 50


def normalize_interests(values: list[str] | None) -> list[str]:
    """
    Cleans up a raw interests list -- whether every entry came from the
    predefined chip list or a user typed some of them in by hand (see
    ProfileSetup's "Add your own interest" field). Applied server-side so
    the rule holds regardless of what the frontend sends:

      - trim surrounding whitespace, collapse internal whitespace to a
        single space (" robotics   design " -> "robotics design")
      - lowercase, matching the predefined options (scoring.py already
        lowercases both sides when comparing, but storing consistently
        avoids "STEM" and "stem" silently existing as two separate tags)
      - drop empties and anything absurdly long (a pasted paragraph, not
        an interest)
      - de-duplicate while preserving first-seen order, so re-adding an
        already-selected interest (predefined or custom) is a no-op
        instead of creating a duplicate entry
    """
    if not values:
        return []

    seen = set()
    normalized = []
    for raw in values:
        if not isinstance(raw, str):
            continue
        cleaned = " ".join(raw.strip().split()).lower()
        if not cleaned or len(cleaned) > _MAX_INTEREST_LENGTH:
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized
