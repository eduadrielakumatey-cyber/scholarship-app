"""
app/services/preferences.py
------------------------------
Layer 4 of the recommendation architecture: a small, capped nudge learned
from a student's own save/like/pass history, so two students with
identical profiles don't get identical rankings forever. This is DB-backed
(reads Interaction + Scholarship), which is why it's separate from the
pure functions in scoring.py.

Deliberately kept small. MAX_BOOST caps the effect at +/-5 points out of a
0-100 final score -- enough to break a near-tie between two similar
options, structurally incapable of promoting a poor match over a strong
one or of overriding eligibility (this module never runs on ineligible
items at all; matching.py only calls it after the eligibility gate).
"""

from app.extensions import db
from app.models import Interaction, Scholarship

# Smoothing constant: with very few (or zero) prior interactions on a tag,
# affinity stays close to 0 (neutral) instead of swinging on one or two
# data points.
_SMOOTHING = 3
MAX_BOOST = 5.0


def get_tag_affinities(user) -> dict[str, float]:
    """
    Returns {tag: affinity}, affinity in [-1, 1], built from how often this
    user has saved/liked vs. passed on scholarships carrying each
    interest/major tag. Computed once per request and reused across every
    candidate scholarship being scored, rather than re-querying per item.
    """
    rows = (
        db.session.query(Interaction.action, Scholarship.interests, Scholarship.majors)
        .join(Scholarship, Scholarship.id == Interaction.scholarship_id)
        .filter(Interaction.user_id == user.id)
        .all()
    )

    positive: dict[str, int] = {}
    negative: dict[str, int] = {}
    for action, interests, majors in rows:
        if action not in ("save", "like", "pass"):
            continue
        bucket = positive if action in ("save", "like") else negative
        for tag in list(interests or []) + list(majors or []):
            tag = tag.strip().lower()
            bucket[tag] = bucket.get(tag, 0) + 1

    affinities = {}
    for tag in set(positive) | set(negative):
        pos = positive.get(tag, 0)
        neg = negative.get(tag, 0)
        affinities[tag] = (pos - neg) / (pos + neg + _SMOOTHING)
    return affinities


def compute_boost(scholarship, affinities: dict[str, float]) -> float:
    """
    Averages this user's affinity across the scholarship's own
    interest/major tags, scaled into [-MAX_BOOST, +MAX_BOOST]. A
    scholarship with no tags, or a user with no relevant history, scores
    exactly 0 -- correctly "no opinion," not a guess dressed up as one.
    """
    tags = [t.strip().lower() for t in list(scholarship.interests or []) + list(scholarship.majors or [])]
    if not tags:
        return 0.0
    relevant = [affinities.get(tag, 0.0) for tag in tags]
    average_affinity = sum(relevant) / len(relevant)
    return round(MAX_BOOST * average_affinity, 2)
