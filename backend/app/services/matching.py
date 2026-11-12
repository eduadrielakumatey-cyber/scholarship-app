"""
app/services/matching.py
--------------------------
Sits between the routes and the scoring engine. Responsible for everything
scoring.py can't do on its own because it needs the database:

  1. Pulling candidate scholarships (active, not expired, and -- for the
     swipe deck specifically -- not already swiped by this user)
  2. Scoring each candidate with services/scoring.py
  3. Normalizing Application Value into a 0-100 PERCENTILE against the
     rest of the user's currently-eligible pool (this is why it can't
     live in scoring.py: percentile requires seeing every candidate at
     once, not one at a time)
  4. Adding the small User Preferences boost from services/preferences.py
  5. Combining everything into FinalScore and sorting

FinalScore = 0.50 * MatchQuality + 0.50 * ApplicationValue + PreferenceBoost,
clamped to [0, 100]. PreferenceBoost is itself already bounded to
[-5, +5] by preferences.py, so it can nudge ordering but never swing the
result by more than a rounding-sized margin.

The SAME reference pool (this user's active, non-expired, eligible
scholarships, independent of swipe history) is used to compute
percentiles everywhere -- Discover, Saved, and the detail view -- so a
scholarship's Application Value score doesn't silently change meaning
depending on which screen it's viewed from.

RECOMMENDATION FRESHNESS -- get_swipe_deck excludes anything the user
has already swiped on, EXCEPT that a "pass" can expire. See
_reentry_ids() below for the exact rule: a skip only gets reconsidered
if the user's interests have since grown to include something that
scholarship is actually tagged with. "save"/"like" never expire -- those
are a deliberate positive choice, not a queue the user should be pulled
back into.
"""

from __future__ import annotations

from datetime import date

from flask import current_app

from app.extensions import db
from app.models import Scholarship, Interaction
from app.services import preferences
from app.services.scoring import calculate_scores

FINAL_SCORE_MATCH_WEIGHT = 0.5
FINAL_SCORE_VALUE_WEIGHT = 0.5


def _active_not_expired_query(today: date):
    query = Scholarship.query.filter(Scholarship.is_active.is_(True)).filter(
        db.or_(Scholarship.deadline.is_(None), Scholarship.deadline >= today)
    )
    # ScholarMatch launches in one state (FOCUS_STATE, "MD"): only awards
    # open to that state's students are shown -- no national or other-state
    # ones. Nothing is deleted; clearing the setting shows everything again.
    focus = current_app.config.get("FOCUS_STATE")
    if focus:
        query = query.filter(Scholarship.states.any(focus))
    # Every card says "Essay required" or "No essay"; a listing whose essay
    # requirement hasn't been confirmed from its official page isn't shown.
    query = query.filter(Scholarship.essay_required.isnot(None))
    return query


def school_options(today: date | None = None) -> dict:
    """The colleges with awards only their own students can get, with how
    many open listings each has, plus how many listings are open to any
    school -- for the "Which colleges?" picker."""
    rows = (
        _active_not_expired_query(today or date.today())
        .with_entities(Scholarship.school, db.func.count())
        .group_by(Scholarship.school)
        .all()
    )
    schools = sorted(({"name": s, "count": n} for s, n in rows if s), key=lambda r: r["name"])
    any_school = sum(n for s, n in rows if not s)
    return {"schools": schools, "any_school_count": any_school}


def _percentile(value: float, pool: list[float]) -> float:
    """
    What fraction of `pool` this value is at or above, as 0-100. Self-
    calibrating -- no invented dollar breakpoints, only ever compares real
    numbers already in the database to each other. An empty pool (e.g. a
    user with no other eligible candidates right now) returns the neutral
    midpoint, the same "no information" rule used throughout Match Quality.
    """
    if not pool:
        return 50.0
    at_or_below = sum(1 for v in pool if v <= value)
    return round(100 * at_or_below / len(pool), 1)


def combine_final_score(match_quality_score: float, application_value_score: float, preference_boost: float) -> float:
    """
    FinalScore = 0.50 * MatchQuality + 0.50 * ApplicationValue + PreferenceBoost,
    clamped to [0, 100]. Pulled out as its own pure function (no DB, no
    model objects) so the combination formula itself -- the single most
    consequential piece of arithmetic in the whole engine -- can be unit
    tested directly, independent of how the two inputs were computed.
    preference_boost is expected to already be bounded to [-5, +5] by
    preferences.py; this function does not re-clamp it individually, only
    the final combined result.
    """
    raw = (
        FINAL_SCORE_MATCH_WEIGHT * match_quality_score
        + FINAL_SCORE_VALUE_WEIGHT * application_value_score
        + preference_boost
    )
    return round(min(max(raw, 0.0), 100.0), 1)


def _build_reference(user, today: date | None = None):
    """
    Computes, once per request: every active/non-expired scholarship this
    user is currently eligible for (scored), the pool of their
    expected-value-per-hour figures (for percentile normalization), and
    this user's tag affinities (for the preference boost). Returns
    (bases_by_id, ev_pool, affinities, today) for reuse by both the deck
    and single/saved scoring paths below.
    """
    today = today or date.today()
    candidates = _active_not_expired_query(today).all()
    affinities = preferences.get_tag_affinities(user)

    bases_by_id = {}
    ev_pool = []
    for scholarship in candidates:
        base = calculate_scores(user, scholarship, today=today)
        bases_by_id[scholarship.id] = base
        if base["eligible"]:
            ev_pool.append(base["application_value_raw"]["expected_value_per_hour"])

    return bases_by_id, ev_pool, affinities, today


def _finalize(scholarship, base: dict, ev_pool: list[float], affinities: dict) -> dict:
    """Turns a scoring.calculate_scores() bundle into the full API payload."""
    payload = scholarship.to_dict()
    payload["eligible"] = base["eligible"]
    payload["urgency"] = base["urgency"]

    if not base["eligible"]:
        payload["ineligible_reasons"] = base["ineligible_reasons"]
        payload["match_quality"] = None
        payload["competitiveness"] = None
        payload["application_value"] = None
        payload["preference_boost"] = None
        payload["final_score"] = None
        return payload

    application_value_score = _percentile(
        base["application_value_raw"]["expected_value_per_hour"], ev_pool
    )
    preference_boost = preferences.compute_boost(scholarship, affinities)
    final_score = combine_final_score(base["match_quality"]["score"], application_value_score, preference_boost)

    payload["match_quality"] = base["match_quality"]
    payload["matched_on"] = base.get("matched_on", [])
    payload["competitiveness"] = base["competitiveness"]
    payload["application_value"] = {**base["application_value_raw"], "score": application_value_score}
    payload["preference_boost"] = preference_boost
    payload["final_score"] = final_score
    return payload


def _normalized_interests(user) -> set[str]:
    return {t.strip().lower() for t in (user.interests or []) if t and t.strip()}


def _reentry_ids(current_interests: set[str], passed_rows: list[tuple]) -> set[int]:
    """
    Decides which "pass"-ed scholarships should re-enter the deck.

    For each passed scholarship, `new_tags` is whatever's in the user's
    CURRENT interests that wasn't there at pass-time (interest_snapshot).
    If that's empty, nothing about this user's interests has changed
    since they passed -- stays excluded. If it's non-empty, the pass only
    "expires" when the scholarship itself is tagged with one of those NEW
    interests -- i.e. the skip was made without the information that now
    makes it relevant, so it deserves a second look.

    This is deliberately narrow: adding one new interest does not dump
    the user's entire pass history back into the deck (no spam), only
    the subset that's actually about the thing they just added. A row
    with no snapshot (interest_snapshot is NULL -- passed before this
    column existed) is treated as an unknown baseline, so any current
    interest counts as "new" for it; that's a one-time reconciliation,
    not a recurring re-show.
    """
    reentry = set()
    for scholarship_id, snapshot, sch_interests in passed_rows:
        baseline = {t.strip().lower() for t in (snapshot or [])}
        new_tags = current_interests - baseline
        if not new_tags:
            continue
        sch_tags = {t.strip().lower() for t in (sch_interests or [])}
        if sch_tags & new_tags:
            reentry.add(scholarship_id)
    return reentry


def _excluded_scholarship_ids(user) -> set[int]:
    """
    Every scholarship id that should be hidden from this user's deck right
    now: everything they've saved/liked (permanent), plus everything
    they've passed on that hasn't earned reentry (see _reentry_ids).
    """
    rows = (
        db.session.query(
            Interaction.scholarship_id, Interaction.action,
            Interaction.interest_snapshot, Scholarship.interests,
        )
        .join(Scholarship, Scholarship.id == Interaction.scholarship_id)
        .filter(Interaction.user_id == user.id)
        .all()
    )

    permanent = {r.scholarship_id for r in rows if r.action in ("save", "like")}
    passed_rows = [
        (r.scholarship_id, r.interest_snapshot, r.interests) for r in rows if r.action == "pass"
    ]
    passed_ids = {sid for sid, _, _ in passed_rows}
    reentry = _reentry_ids(_normalized_interests(user), passed_rows)

    return permanent | (passed_ids - reentry)


def _reason_category(reason: str) -> str:
    """Collapse is_eligible()'s specific reasons into a few readable buckets."""
    if reason.startswith("Only for students at"):
        return "Only for students at other colleges"
    if "GPA" in reason:
        return "GPA below the minimum"
    if "your state" in reason:
        return "Only for students in other states"
    if reason.startswith("Not open to"):
        return "Not open to your grade level"
    if "demographic" in reason:
        return "For a specific background not on your profile"
    if "majors" in reason:
        return "Restricted to other majors"
    return "Other requirements"


def get_swipe_deck(user, limit: int = 25) -> list[dict]:
    return get_swipe_deck_with_summary(user, limit)[0]


def get_swipe_deck_with_summary(user, limit: int = 25) -> tuple[list[dict], dict]:
    """
    Same as get_swipe_deck, plus a summary of the open scholarships the
    filter hid and why, so a short deck reads as "we filtered for you"
    rather than "there's nothing here".
    """
    cards, hidden = _deck(user, limit)
    counts: dict[str, int] = {}
    for reasons in hidden:
        for category in {_reason_category(r) for r in reasons}:
            counts[category] = counts.get(category, 0) + 1
    summary = {
        "hidden_count": len(hidden),
        "reasons": [
            {"label": label, "count": n}
            for label, n in sorted(counts.items(), key=lambda kv: -kv[1])
        ],
    }
    return cards, summary


def _deck(user, limit: int) -> tuple[list[dict], list[list[str]]]:
    """
    Returns scored, ranked scholarship dicts for the next batch of swipe
    cards. Excludes anything the user has saved/liked, and anything
    they've passed on that hasn't earned reentry under the freshness rule
    above, plus anything inactive or past its deadline. Ineligible
    candidates are dropped entirely -- Layer 1 (Hard Eligibility) never
    lets them reach ranking.
    """
    today = date.today()
    excluded_ids = _excluded_scholarship_ids(user)

    query = _active_not_expired_query(today)
    if excluded_ids:
        query = query.filter(~Scholarship.id.in_(excluded_ids))
    candidates = query.all()

    affinities = preferences.get_tag_affinities(user)
    scored_bases = []
    ev_pool = []
    hidden = []
    for scholarship in candidates:
        base = calculate_scores(user, scholarship, today=today)
        if not base["eligible"]:
            hidden.append(base.get("ineligible_reasons") or [])
            continue
        scored_bases.append((scholarship, base))
        ev_pool.append(base["application_value_raw"]["expected_value_per_hour"])

    results = [_finalize(s, b, ev_pool, affinities) for s, b in scored_bases]
    results.sort(key=lambda card: card["final_score"], reverse=True)
    return results[:limit], hidden


def score_single(user, scholarship) -> dict:
    """Used by the scholarship-detail endpoint to score one item on demand."""
    bases_by_id, ev_pool, affinities, today = _build_reference(user)
    base = bases_by_id.get(scholarship.id) or calculate_scores(user, scholarship, today=today)
    return _finalize(scholarship, base, ev_pool, affinities)


def score_saved_list(user, scholarships: list[Scholarship]) -> list[dict]:
    """
    Used by GET /api/saved. Scores a set of already-saved scholarships
    against the SAME reference pool used by score_single/get_swipe_deck,
    so Application Value percentiles mean the same thing on every screen.
    A saved item that has since become ineligible or expired is still
    returned (with eligible=False) rather than dropped -- the student
    saved it on purpose and should still be able to see and manage it.
    """
    bases_by_id, ev_pool, affinities, today = _build_reference(user)
    results = []
    for scholarship in scholarships:
        base = bases_by_id.get(scholarship.id) or calculate_scores(user, scholarship, today=today)
        results.append(_finalize(scholarship, base, ev_pool, affinities))
    return results


def get_match_counts(user, strong_threshold: float = 70.0) -> dict:
    """
    Used by the stats page ("You currently have N scholarships that
    strongly match your profile"). Reuses _build_reference -- the same
    eligible-candidate pool the deck/saved/detail screens score against --
    so this number can never disagree with what the user actually sees
    when they open Discover. Independent of swipe history on purpose:
    it answers "how many things fit me right now," not "how many are
    left in my queue."
    """
    bases_by_id, _ev_pool, _affinities, _today = _build_reference(user)
    eligible_bases = [b for b in bases_by_id.values() if b["eligible"]]
    strong = sum(1 for b in eligible_bases if b["match_quality"]["score"] >= strong_threshold)
    return {"eligible_count": len(eligible_bases), "strong_match_count": strong}
