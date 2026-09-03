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
