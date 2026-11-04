"""
app/services/scoring.py
--------------------------
Pure, DB-free scoring for a single (user, scholarship) pair. No database
access happens in this file on purpose -- it keeps every function trivially
unit-testable with plain SimpleNamespace stand-ins (see tests/test_scoring.py)
and keeps app/services/matching.py the only place that has to think about
querying, batching, or ordering.

This implements the four-layer recommendation architecture:

  1. HARD ELIGIBILITY  (is_eligible)       -- binary. Never weighted, never
     fuzzy. If it fails, the scholarship should not be scored further.

  2. MATCH QUALITY     (match_quality)     -- 0-100, exactly three
     components (Academic Fit, Major Alignment, Interest Alignment).
     Grade level, state, and demographics are deliberately NOT re-scored
     here: they're already hard eligibility gates, and a fact strict
     enough to gate on doesn't need to also be a soft ranking bonus --
     that would just be scoring the same yes/no answer twice. Everywhere
     a component "doesn't apply" to a given scholarship, it scores exactly
     50 (the literal midpoint of the scale) -- one universal rule for "no
     information," not a different hand-picked number per component.

  3. APPLICATION VALUE (competitiveness_estimate, application_value_raw)
     -- built from award_amount, estimated_hours_to_apply,
     estimated_applicant_pool, and num_awards. Deliberately does NOT
     include a probability-of-winning: there is no outcome data (who
     applied, who won) to calibrate one, so this only ever computes and
     labels a transparent competitiveness RATIO, never a percent chance.
     The percentile-based normalization into a 0-100 score happens in
     matching.py, since it requires comparing against the rest of a
     user's eligible candidate pool -- that's cross-row information this
     file intentionally doesn't have.

  4. URGENCY (urgency_classification) -- computed here because it's a
     pure function of a deadline and today's date, but it is NEVER
     allowed to change award_amount, competitiveness, or application
     value. It's a separate classification for display/prioritization
     only. See the recommendation-architecture design notes for why.

USER PREFERENCES (the 4th architecture layer) lives in
app/services/preferences.py instead, because it requires querying
Interaction history -- also cross-row, DB-backed information this file
doesn't touch.
"""

from __future__ import annotations

from datetime import date

from app.services import interest_taxonomy


def _safe_lower_set(values: list[str] | None) -> set[str]:
    return {v.strip().lower() for v in values} if values else set()


# Mirrors frontend/src/constants/gradeLevels.js -- kept in sync manually
# since it's a tiny, rarely-changing display lookup, not shared code.
_GRADE_LEVEL_LABELS = {
    "12": "High School Senior",
    "college_1": "College Freshman",
    "college_2": "College Sophomore",
    "college_3": "College Junior",
    "college_4": "College Senior",
    "college_5plus": "5th Year+ / Graduate Student",
}


def _grade_level_label(value: str | None) -> str:
    return _GRADE_LEVEL_LABELS.get(value, value or "")


# ---------------------------------------------------------------------------
# Layer 1: Hard Eligibility
# ---------------------------------------------------------------------------

def is_eligible(user, scholarship) -> tuple[bool, list[str]]:
    """
    Returns (eligible, reasons). `reasons` is empty when eligible, and a
    list of plain-English explanations for every failed check when not --
    used both for debugging and for the explainability payload when a
    saved/previously-eligible item later becomes ineligible.
    """
    reasons = []

    if scholarship.min_gpa is not None and user.gpa is not None and user.gpa < scholarship.min_gpa:
        reasons.append(f"Your GPA ({user.gpa:g}) is below the {scholarship.min_gpa:g} minimum")

    grade_levels = _safe_lower_set(scholarship.grade_levels)
    if grade_levels and user.grade_level and user.grade_level.lower() not in grade_levels:
        reasons.append(f"Not open to {_grade_level_label(user.grade_level)}")

    states = _safe_lower_set(scholarship.states)
    if states and user.state and user.state.lower() not in states:
        reasons.append(f"Not open to your state ({user.state})")

    required_demo = _safe_lower_set(scholarship.demographics)
    if required_demo:
        user_demo = _safe_lower_set(user.demographics)
        if not (required_demo & user_demo):
            reasons.append("Requires a demographic group not on your profile")

    # Major is only a HARD gate when the scholarship is explicitly flagged
    # as legally/structurally major-restricted. Otherwise a mismatch is a
    # Match Quality signal, not a disqualification -- see major_alignment().
    if getattr(scholarship, "majors_are_hard_requirement", False):
        required_majors = _safe_lower_set(scholarship.majors)
        if required_majors and user.major and user.major.lower() not in required_majors:
            reasons.append(f"Restricted to majors: {', '.join(sorted(required_majors))}")

    return (len(reasons) == 0, reasons)


# ---------------------------------------------------------------------------
# Layer 2: Match Quality
# ---------------------------------------------------------------------------

NO_INFO_SCORE = 50.0  # the universal "doesn't apply / unknown" score for every component

_GPA_WEIGHT = 30
_MAJOR_WEIGHT = 40
_INTEREST_WEIGHT = 30


def _academic_fit(user, scholarship) -> dict:
    if scholarship.min_gpa is None or user.gpa is None:
        reason = "No GPA requirement" if scholarship.min_gpa is None else "GPA not on your profile"
        return {"name": "Academic fit", "score": NO_INFO_SCORE, "weight": _GPA_WEIGHT, "reason": reason}

    headroom = user.gpa - scholarship.min_gpa
    # One deliberately-labeled judgment call: a full GPA point of headroom
    # above the minimum counts as "clearly exceeds the bar" and saturates
    # the score. Everything below that scales linearly from 50 (exactly at
    # the minimum) to 100.
    score = round(min(50 + 50 * min(headroom / 1.0, 1.0), 100.0), 1)
    if headroom <= 0:
        reason = f"Your GPA exactly meets the {scholarship.min_gpa:g} minimum"
    else:
        reason = f"Your GPA is {headroom:.1f} above the {scholarship.min_gpa:g} minimum"
    return {"name": "Academic fit", "score": score, "weight": _GPA_WEIGHT, "reason": reason}


def _major_alignment(user, scholarship) -> dict:
    required_majors = _safe_lower_set(scholarship.majors)
    if not required_majors:
        return {"name": "Major alignment", "score": NO_INFO_SCORE, "weight": _MAJOR_WEIGHT,
                "reason": "Open to all majors"}

    if getattr(scholarship, "majors_are_hard_requirement", False):
        # Already gated true by is_eligible() to even be scored here.
        return {"name": "Major alignment", "score": 100.0, "weight": _MAJOR_WEIGHT,
                "reason": f"Restricted to and matches your major: {scholarship.majors[0]}"}

    if not user.major:
        return {"name": "Major alignment", "score": NO_INFO_SCORE, "weight": _MAJOR_WEIGHT,
                "reason": "Major not on your profile"}

    if user.major.lower() in required_majors:
        return {"name": "Major alignment", "score": 100.0, "weight": _MAJOR_WEIGHT,
                "reason": f"Matches your major: {user.major}"}

    # Soft mismatch: not gated (majors_are_hard_requirement is False), so
    # still shown -- just ranked low on this component. No invented
    # "related field" middle tier: that would need a majors taxonomy we
    # don't have, and guessing "70" for "kind of related" is exactly the
    # sort of unjustified constant this design avoids.
    return {"name": "Major alignment", "score": 0.0, "weight": _MAJOR_WEIGHT,
            "reason": f"Lists {', '.join(scholarship.majors)}, not your major ({user.major})"}


def _interest_alignment(user, scholarship) -> dict:
    sch_interests = _safe_lower_set(scholarship.interests)
    if not sch_interests:
        return {"name": "Interest alignment", "score": NO_INFO_SCORE, "weight": _INTEREST_WEIGHT,
                "reason": "No listed interests"}

    user_interests = _safe_lower_set(user.interests)
    exact_overlap = sch_interests & user_interests

    # A niche/custom interest (e.g. "semiconductor design", "cybersecurity"
    # -- see ProfileSetup's free-text interest field) should still credit
    # a scholarship tagged with the broader category it belongs to
    # ("engineering", "computer science"), not score zero just because the
    # exact strings differ. interest_taxonomy.expand() adds those broader
    # categories on top of the user's raw interests; anything matched only
    # through that expansion is tracked separately so the explanation can
    # say so, but counts the same toward the score -- the scholarship IS
    # about that broader thing, and the user's interest IS a form of it.
    expanded_user_interests = interest_taxonomy.expand(user_interests)
    broader_overlap = (sch_interests & expanded_user_interests) - exact_overlap

    overlap = exact_overlap | broader_overlap
    score = round(100 * len(overlap) / len(sch_interests), 1)
    if overlap:
        parts = sorted(exact_overlap) + [f"{tag} (related interest)" for tag in sorted(broader_overlap)]
        reason = f"{len(overlap)} of {len(sch_interests)} listed interests match ({', '.join(parts)})"
    else:
        reason = "None of your listed interests match"
    return {"name": "Interest alignment", "score": score, "weight": _INTEREST_WEIGHT, "reason": reason}


def _match_quality_label(score: float) -> str:
    if score >= 85:
        return "Excellent fit"
    if score >= 70:
        return "Strong fit"
    if score >= 55:
        return "Good fit"
    return "Fair fit"


def match_quality(user, scholarship) -> dict:
    """
    Returns {"score": 0-100, "label": str, "components": [...]}.
    Weights are fixed and independent of which criteria a given
    scholarship happens to specify -- this is what stops a scholarship
    with almost no listed restrictions from artificially maxing out just
    because it has fewer, more heavily-weighted components to clear.
    """
    components = [
        _academic_fit(user, scholarship),
        _major_alignment(user, scholarship),
        _interest_alignment(user, scholarship),
    ]
    total_weight = sum(c["weight"] for c in components)  # always 100 by construction
    score = round(sum(c["score"] * c["weight"] for c in components) / total_weight, 1)
    return {"score": score, "label": _match_quality_label(score), "components": components}


# ---------------------------------------------------------------------------
# Layer 3: Application Value
# ---------------------------------------------------------------------------

def competitiveness_estimate(scholarship) -> dict:
    """
    Deliberately NOT a probability of winning -- there's no historical
    outcome data (who applied, who won) to calibrate one, so calling it a
    probability would overstate what we actually know. This is a
    transparent ratio of awards given to the (rough, source-estimated)
    applicant pool -- nothing more.
    """
    num_awards = max(int(scholarship.num_awards or 1), 1)
    pool = max(int(scholarship.estimated_applicant_pool or 0), num_awards)  # sanity floor, not a tuning knob
    ratio = num_awards / pool
    one_in = round(1 / ratio) if ratio > 0 else None
    display = f"~1 in {one_in} (estimated)" if one_in else "Not enough data to estimate"
    return {"ratio": round(ratio, 4), "one_in": one_in, "display": display}


def application_value_raw(scholarship, competitiveness_ratio: float) -> dict:
    """
    Dollar figures only -- amount, effort, and (via expected_value_per_hour)
    competitiveness. Not yet normalized to 0-100; that requires comparing
    against a user's other eligible scholarships, which happens in
    matching.py.
    """
    amount = float(scholarship.award_amount or 0)
    hours = max(float(scholarship.estimated_hours_to_apply or 1), 0.25)
    dollars_per_hour_if_won = round(amount / hours, 2)
    expected_value = round(amount * competitiveness_ratio, 2)
    expected_value_per_hour = round(expected_value / hours, 2)
    return {
        "dollars_per_hour_if_won": dollars_per_hour_if_won,
        "expected_value": expected_value,
        "expected_value_per_hour": expected_value_per_hour,
    }


# ---------------------------------------------------------------------------
# Urgency -- classification only, never touches value
# ---------------------------------------------------------------------------

def urgency_classification(deadline, today: date | None = None) -> dict:
    """
    A pure calendar fact, kept completely separate from award value. The
    breakpoints below are a display/grouping judgment (like the Match
    Quality label bands), not a calculation -- they decide which of four
    words to show and, in matching.py, how to break near-ties in ranking.
    They never adjust award_amount, competitiveness, or application value.
    """
    today = today or date.today()
    if deadline is None:
        return {"class": "normal", "days_left": None}

    days_left = (deadline - today).days
    if days_left <= 3:
        cls = "critical"
    elif days_left <= 14:
        cls = "urgent"
    elif days_left <= 30:
        cls = "approaching"
    else:
        cls = "normal"
    return {"class": cls, "days_left": days_left}


# ---------------------------------------------------------------------------
# Bundle: everything that can be computed without touching the database
# ---------------------------------------------------------------------------

def calculate_scores(user, scholarship, today: date | None = None) -> dict:
    """
    Per-(user, scholarship) bundle. Does NOT include the percentile-based
    Application Value score, the User Preferences boost, or the combined
    FinalScore -- those need the rest of the user's candidate pool and
    their interaction history, both DB-backed, and are assembled by
    app/services/matching.py.
    """
    eligible, reasons = is_eligible(user, scholarship)
    urgency = urgency_classification(scholarship.deadline, today=today)

    if not eligible:
        return {
            "eligible": False,
            "ineligible_reasons": reasons,
            "match_quality": None,
            "competitiveness": None,
            "application_value_raw": None,
            "urgency": urgency,
        }

    competitiveness = competitiveness_estimate(scholarship)
    return {
        "eligible": True,
        "ineligible_reasons": [],
        "match_quality": match_quality(user, scholarship),
        "matched_on": matched_on(user, scholarship),
        "competitiveness": competitiveness,
        "application_value_raw": application_value_raw(scholarship, competitiveness["ratio"]),
        "urgency": urgency,
    }


# ---------------------------------------------------------------------------
# "Matched because" chips
# ---------------------------------------------------------------------------

def matched_on(user, scholarship) -> list[str]:
    """
    Short, concrete reasons this (already eligible) scholarship was shown,
    e.g. ["State: MD", "Interest: biology"], so the student can see the
    filter working instead of taking the ranking on faith. Only lists
    restrictions the scholarship actually has and the profile actually
    meets; an award open to everyone says so.
    """
    chips = []
    states = _safe_lower_set(scholarship.states)
    if states and user.state and user.state.lower() in states:
        chips.append(f"State: {user.state.upper()}")

    grades = _safe_lower_set(scholarship.grade_levels)
    if grades and user.grade_level and user.grade_level.lower() in grades:
        chips.append(f"Grade: {_grade_level_label(user.grade_level)}")

    if scholarship.min_gpa is not None and user.gpa is not None and user.gpa >= scholarship.min_gpa:
        chips.append(f"GPA: {user.gpa:g} (min {scholarship.min_gpa:g})")

    majors = _safe_lower_set(scholarship.majors)
    if majors and user.major and user.major.lower() in majors:
        chips.append(f"Major: {user.major}")

    shared_demo = _safe_lower_set(scholarship.demographics) & _safe_lower_set(user.demographics)
    for group in sorted(shared_demo)[:2]:
        chips.append(f"Background: {group}")

    sch_interests = _safe_lower_set(scholarship.interests)
    user_interests = _safe_lower_set(user.interests)
    exact = sch_interests & user_interests
    related = (sch_interests & interest_taxonomy.expand(user_interests)) - exact
    for tag in sorted(exact)[:2]:
        chips.append(f"Interest: {tag}")
    if not exact:
        for tag in sorted(related)[:1]:
            chips.append(f"Interest: {tag} (related)")

    if not chips:
        chips.append("Open to all students")
    return chips
