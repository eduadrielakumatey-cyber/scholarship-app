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
"""

from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models import Scholarship, Interaction
from app.services import preferences
from app.services.scoring import calculate_scores

FINAL_SCORE_MATCH_WEIGHT = 0.5
FINAL_SCORE_VALUE_WEIGHT = 0.5


def _active_not_expired_query(today: date):
    return Scholarship.query.filter(Scholarship.is_active.is_(True)).filter(
        db.or_(Scholarship.deadline.is_(None), Scholarship.deadline >= today)
    )


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
    payload["competitiveness"] = base["competitiveness"]
    payload["application_value"] = {**base["application_value_raw"], "score": application_value_score}
    payload["preference_boost"] = preference_boost
    payload["final_score"] = final_score
    return payload


def get_swipe_deck(user, limit: int = 25) -> list[dict]:
    """
    Returns scored, ranked scholarship dicts for the next batch of swipe
    cards. Excludes anything the user has already swiped on (like/pass/
    save) and anything inactive or past its deadline. Ineligible
    candidates are dropped entirely -- Layer 1 (Hard Eligibility) never
    lets them reach ranking.
    """
    today = date.today()
    already_seen_ids = [
        row.scholarship_id for row in Interaction.query.filter_by(user_id=user.id).all()
    ]

    query = _active_not_expired_query(today)
    if already_seen_ids:
        query = query.filter(~Scholarship.id.in_(already_seen_ids))
    candidates = query.all()

    affinities = preferences.get_tag_affinities(user)
    scored_bases = []
    ev_pool = []
    for scholarship in candidates:
        base = calculate_scores(user, scholarship, today=today)
        if not base["eligible"]:
            continue
        scored_bases.append((scholarship, base))
        ev_pool.append(base["application_value_raw"]["expected_value_per_hour"])

    results = [_finalize(s, b, ev_pool, affinities) for s, b in scored_bases]
    results.sort(key=lambda card: card["final_score"], reverse=True)
    return results[:limit]


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
