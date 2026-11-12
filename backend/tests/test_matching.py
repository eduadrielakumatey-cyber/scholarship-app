"""
tests/test_matching.py
------------------------
Unit tests for the pieces of app/services/matching.py that don't require a
database: percentile normalization (Application Value) and the FinalScore
combination formula. These are pure functions taking plain numbers, so
they're tested directly rather than through a live Scholarship/User model.

app/services/matching.py's DB-backed functions (get_swipe_deck,
score_single, score_saved_list) are exercised instead through live
verification against the running dev database -- see the implementation
report. The project's SQLite test config can't create the Postgres-only
ARRAY-typed columns these models use (a pre-existing gap, not introduced
here), so a full in-process DB integration test isn't set up; that's
called out explicitly as a known limitation rather than worked around.

Run with:
    cd backend
    pytest
"""

from app.services.matching import _percentile, combine_final_score
from app.services.preferences import MAX_BOOST, compute_boost
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# _percentile
# ---------------------------------------------------------------------------

class TestPercentile:
    def test_empty_pool_returns_neutral_midpoint(self):
        assert _percentile(100.0, []) == 50.0

    def test_lowest_value_in_pool_scores_low(self):
        pool = [10.0, 50.0, 100.0]
        assert _percentile(10.0, pool) == round(100 / 3, 1)

    def test_highest_value_in_pool_scores_100(self):
        pool = [10.0, 50.0, 100.0]
        assert _percentile(100.0, pool) == 100.0

    def test_all_equal_values_score_100(self):
        pool = [50.0, 50.0, 50.0]
        assert _percentile(50.0, pool) == 100.0

    def test_value_below_entire_pool_scores_zero(self):
        pool = [50.0, 60.0, 70.0]
        assert _percentile(10.0, pool) == 0.0


# ---------------------------------------------------------------------------
# combine_final_score -- the FinalScore formula itself
# ---------------------------------------------------------------------------

class TestCombineFinalScore:
    def test_equal_weight_on_match_and_value(self):
        # 100 match / 0 value should land exactly at the midpoint of what
        # 50/50 weighting implies, with no preference boost.
        assert combine_final_score(100.0, 0.0, 0.0) == 50.0
        assert combine_final_score(0.0, 100.0, 0.0) == 50.0

    def test_max_inputs_with_max_boost_clamps_at_100(self):
        assert combine_final_score(100.0, 100.0, MAX_BOOST) == 100.0

    def test_min_inputs_with_negative_boost_clamps_at_zero(self):
        assert combine_final_score(0.0, 0.0, -MAX_BOOST) == 0.0

    def test_preference_boost_cannot_overcome_a_large_gap(self):
        """Structural guarantee from the design: preference can nudge a
        near-tie, but a +5 boost must never let a poor match/value pairing
        outrank a genuinely much stronger one."""
        weak_but_boosted = combine_final_score(20.0, 20.0, MAX_BOOST)
        strong_unboosted = combine_final_score(80.0, 80.0, 0.0)
        assert strong_unboosted > weak_but_boosted

    def test_typical_midrange_values(self):
        # 0.5*70 + 0.5*60 + 2 = 35 + 30 + 2 = 67
        assert combine_final_score(70.0, 60.0, 2.0) == 67.0


# ---------------------------------------------------------------------------
# preferences.compute_boost (pure given a precomputed affinities dict)
# ---------------------------------------------------------------------------

def make_scholarship(**overrides):
    defaults = dict(interests=["stem"], majors=["computer science"])
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestPreferenceBoost:
    def test_no_history_scores_zero(self):
        scholarship = make_scholarship()
        assert compute_boost(scholarship, affinities={}) == 0.0

    def test_no_tags_scores_zero_even_with_history(self):
        scholarship = make_scholarship(interests=[], majors=[])
        assert compute_boost(scholarship, affinities={"stem": 1.0}) == 0.0

    def test_positive_affinity_gives_positive_boost(self):
        scholarship = make_scholarship(interests=["stem"], majors=[])
        boost = compute_boost(scholarship, affinities={"stem": 1.0})
        assert boost == MAX_BOOST

    def test_negative_affinity_gives_negative_boost(self):
        scholarship = make_scholarship(interests=["stem"], majors=[])
        boost = compute_boost(scholarship, affinities={"stem": -1.0})
        assert boost == -MAX_BOOST

    def test_boost_never_exceeds_cap_in_either_direction(self):
        scholarship = make_scholarship(interests=["stem", "coding", "robotics"], majors=["computer science"])
        boost = compute_boost(scholarship, affinities={
            "stem": 1.0, "coding": 1.0, "robotics": 1.0, "computer science": 1.0,
        })
        assert -MAX_BOOST <= boost <= MAX_BOOST

    def test_unseen_tag_defaults_to_neutral_zero_affinity(self):
        scholarship = make_scholarship(interests=["healthcare"], majors=[])
        # "healthcare" has no entry in affinities -- must be treated as 0,
        # not KeyError, not assumed negative or positive.
        assert compute_boost(scholarship, affinities={"stem": 1.0}) == 0.0


class TestReasonCategory:
    """The 'we hid N scholarships' breakdown buckets is_eligible()'s reasons."""

    def test_each_reason_maps_to_its_bucket(self):
        from app.services.matching import _reason_category

        assert _reason_category("Your GPA (3.1) is below the 3.5 minimum") == "GPA below the minimum"
        assert _reason_category("Not open to your state (MD)") == "Only for students in other states"
        assert _reason_category("Not open to high school seniors") == "Not open to your grade level"
        assert _reason_category("Requires a demographic group not on your profile").startswith("For a specific")
        assert _reason_category("Restricted to majors: nursing") == "Restricted to other majors"
        assert _reason_category("Only for students at Towson University") == "Only for students at other colleges"
