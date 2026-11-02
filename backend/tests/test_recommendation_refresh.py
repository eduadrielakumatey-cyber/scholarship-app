"""
tests/test_recommendation_refresh.py
--------------------------------------
Unit tests for the DB-free pieces of the interest-change recommendation
refresh: normalize_interests() (app/utils/validators.py) and
_reentry_ids() (app/services/matching.py), which decides which
previously-passed scholarships should re-enter a user's swipe deck after
their interests change. Both are pure functions over plain data, so
(per this project's existing testing convention -- see
tests/test_matching.py) they're tested directly rather than through a
live database.

Run with:
    cd backend
    pytest
"""

from app.services.matching import _reentry_ids
from app.utils.validators import normalize_interests


class TestNormalizeInterests:
    def test_trims_and_lowercases(self):
        assert normalize_interests([" Robotics  Design "]) == ["robotics design"]

    def test_collapses_internal_whitespace(self):
        assert normalize_interests(["semiconductor    design"]) == ["semiconductor design"]

    def test_deduplicates_case_and_whitespace_insensitively(self):
        assert normalize_interests(["Robotics", "robotics", "  robotics  "]) == ["robotics"]

    def test_preserves_first_seen_order(self):
        assert normalize_interests(["b", "a", "b", "c"]) == ["b", "a", "c"]

    def test_drops_empty_and_non_string_entries(self):
        assert normalize_interests(["stem", "", "   ", None, 42]) == ["stem"]

    def test_drops_absurdly_long_entries(self):
        huge = "x" * 51
        assert normalize_interests([huge, "stem"]) == ["stem"]

    def test_none_input_returns_empty_list(self):
        assert normalize_interests(None) == []


class TestReentryIds:
    def test_no_interest_change_stays_excluded(self):
        passed_rows = [(1, ["stem"], ["robotics"])]
        assert _reentry_ids({"stem"}, passed_rows) == set()

    def test_new_interest_matching_scholarship_tags_reenters(self):
        # User passed on a robotics scholarship back when they only had
        # "stem"; they've since added "robotics" itself.
        passed_rows = [(1, ["stem"], ["robotics"])]
        assert _reentry_ids({"stem", "robotics"}, passed_rows) == {1}

    def test_new_interest_not_matching_scholarship_stays_excluded(self):
        # New interest is unrelated to this scholarship -- no spam.
        passed_rows = [(1, ["stem"], ["robotics"])]
        assert _reentry_ids({"stem", "music"}, passed_rows) == set()

    def test_null_snapshot_treated_as_unknown_baseline(self):
        # Pre-migration rows have no snapshot; any current interest that
        # matches the scholarship's tags is enough to reconsider it once.
        passed_rows = [(1, None, ["robotics"])]
        assert _reentry_ids({"robotics"}, passed_rows) == {1}

    def test_scholarship_with_no_tags_never_reenters(self):
        passed_rows = [(1, ["stem"], [])]
        assert _reentry_ids({"stem", "robotics"}, passed_rows) == set()

    def test_only_the_relevant_scholarship_reenters_not_the_whole_history(self):
        passed_rows = [
            (1, ["stem"], ["robotics"]),   # relevant to the new "robotics" interest
            (2, ["stem"], ["music"]),      # not relevant -- stays excluded
        ]
        assert _reentry_ids({"stem", "robotics"}, passed_rows) == {1}

    def test_removing_an_interest_produces_no_new_tags(self):
        # Interests shrinking can't surface anything -- there's nothing
        # "new" for the scholarship to match against.
        passed_rows = [(1, ["stem", "music"], ["music"])]
        assert _reentry_ids({"stem"}, passed_rows) == set()
