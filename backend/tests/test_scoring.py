"""
tests/test_scoring.py
------------------------
Unit tests for the pure scoring logic in app/services/scoring.py. These
don't touch the database or Flask at all -- they build lightweight fake
objects with the same attributes the real User/Scholarship models have,
which keeps the tests fast and focused only on the math.

Organized by architecture layer:
  - TestHardEligibility     (Layer 1)
  - TestMatchQuality        (Layer 2)
  - TestCompetitivenessAndValue (Layer 3, minus percentile normalization
    which lives in matching.py and is covered in test_matching.py)
  - TestUrgency             (separate from value, per design)
  - TestCalculateScoresBundle

Run with:
    cd backend
    pytest
"""

from datetime import date, timedelta
from types import SimpleNamespace

from app.services.scoring import (
    calculate_scores,
    competitiveness_estimate,
    is_eligible,
    match_quality,
    urgency_classification,
)


def make_user(**overrides):
    defaults = dict(
        gpa=3.6,
        grade_level="college_2",
        state="MD",
        demographics=["first-generation"],
        interests=["stem", "robotics"],
        major="computer science",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_scholarship(**overrides):
    defaults = dict(
        award_amount=2000,
        deadline=None,
        min_gpa=3.0,
        grade_levels=["12", "college_1", "college_2"],
        states=[],
        demographics=[],
        majors=["computer science"],
        majors_are_hard_requirement=False,
        interests=["stem"],
        estimated_hours_to_apply=2.0,
        estimated_applicant_pool=1000,
        num_awards=5,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Layer 1: Hard Eligibility
# ---------------------------------------------------------------------------

class TestHardEligibility:
    def test_ineligible_when_gpa_too_low(self):
        user = make_user(gpa=2.0)
        scholarship = make_scholarship(min_gpa=3.0)
        eligible, reasons = is_eligible(user, scholarship)
        assert eligible is False
        assert any("GPA" in r for r in reasons)

    def test_ineligible_when_grade_level_excluded(self):
        user = make_user(grade_level="college_4")
        scholarship = make_scholarship(grade_levels=["12", "college_1"])  # e.g. entering-freshman-only
        eligible, reasons = is_eligible(user, scholarship)
        assert eligible is False
        assert any("Not open to" in r for r in reasons)

    def test_ineligible_reason_uses_friendly_grade_label(self):
        """The eligibility reason should read as 'College Senior', not the
        raw internal code 'college_4' -- this is user-facing copy."""
        user = make_user(grade_level="college_4")
        scholarship = make_scholarship(grade_levels=["12", "college_1"])
        _, reasons = is_eligible(user, scholarship)
        assert any("College Senior" in r for r in reasons)
        assert not any("college_4" in r for r in reasons)

    def test_eligible_when_no_restrictions_match(self):
        user = make_user()
        scholarship = make_scholarship()
        eligible, reasons = is_eligible(user, scholarship)
        assert eligible is True
        assert reasons == []

    def test_major_mismatch_is_eligible_when_not_hard_required(self):
        """The core Layer 1 redesign: a major mismatch is a soft signal
        (Match Quality), not a hard exclusion, unless explicitly flagged."""
        user = make_user(major="fine arts")
        scholarship = make_scholarship(majors=["computer science"], majors_are_hard_requirement=False)
        eligible, reasons = is_eligible(user, scholarship)
        assert eligible is True

    def test_major_mismatch_is_ineligible_when_hard_required(self):
        user = make_user(major="fine arts")
        scholarship = make_scholarship(majors=["computer science"], majors_are_hard_requirement=True)
        eligible, reasons = is_eligible(user, scholarship)
        assert eligible is False
        assert any("major" in r.lower() for r in reasons)

    def test_demographic_requires_at_least_one_overlap(self):
        user = make_user(demographics=["veteran"])
        scholarship = make_scholarship(demographics=["first-generation", "hispanic"])
        eligible, reasons = is_eligible(user, scholarship)
        assert eligible is False

    def test_demographic_partial_overlap_is_eligible(self):
        user = make_user(demographics=["first-generation", "veteran"])
        scholarship = make_scholarship(demographics=["first-generation", "hispanic"])
        eligible, _ = is_eligible(user, scholarship)
        assert eligible is True

    def test_state_restriction_blocks_non_matching_state(self):
        user = make_user(state="CA")
        scholarship = make_scholarship(states=["MD", "VA"])
        eligible, reasons = is_eligible(user, scholarship)
        assert eligible is False

    def test_missing_user_gpa_does_not_block_eligibility(self):
        """A profile field left blank shouldn't itself cause exclusion --
        eligibility only fails on a *known* violation."""
        user = make_user(gpa=None)
        scholarship = make_scholarship(min_gpa=3.5)
        eligible, _ = is_eligible(user, scholarship)
        assert eligible is True


# ---------------------------------------------------------------------------
# Layer 2: Match Quality
# ---------------------------------------------------------------------------

class TestMatchQuality:
    def test_score_is_bounded_0_to_100(self):
        user = make_user()
        scholarship = make_scholarship()
        result = match_quality(user, scholarship)
        assert 0 <= result["score"] <= 100

    def test_three_components_always_present_with_fixed_weights(self):
        user = make_user()
        scholarship = make_scholarship()
        result = match_quality(user, scholarship)
        names = {c["name"] for c in result["components"]}
        assert names == {"Academic fit", "Major alignment", "Interest alignment"}
        weights = {c["name"]: c["weight"] for c in result["components"]}
        assert weights == {"Academic fit": 30, "Major alignment": 40, "Interest alignment": 30}

    def test_no_gpa_requirement_scores_neutral_midpoint(self):
        user = make_user()
        scholarship = make_scholarship(min_gpa=None)
        result = match_quality(user, scholarship)
        academic = next(c for c in result["components"] if c["name"] == "Academic fit")
        assert academic["score"] == 50.0

    def test_gpa_exactly_at_minimum_scores_50(self):
        user = make_user(gpa=3.0)
        scholarship = make_scholarship(min_gpa=3.0)
        result = match_quality(user, scholarship)
        academic = next(c for c in result["components"] if c["name"] == "Academic fit")
        assert academic["score"] == 50.0

    def test_gpa_one_point_above_minimum_saturates_at_100(self):
        user = make_user(gpa=4.0)
        scholarship = make_scholarship(min_gpa=3.0)
        result = match_quality(user, scholarship)
        academic = next(c for c in result["components"] if c["name"] == "Academic fit")
        assert academic["score"] == 100.0

    def test_gpa_more_than_one_point_above_does_not_exceed_100(self):
        user = make_user(gpa=5.0)
        scholarship = make_scholarship(min_gpa=3.0)
        result = match_quality(user, scholarship)
        academic = next(c for c in result["components"] if c["name"] == "Academic fit")
        assert academic["score"] == 100.0

    def test_major_exact_match_scores_100(self):
        user = make_user(major="computer science")
        scholarship = make_scholarship(majors=["computer science"], majors_are_hard_requirement=False)
        result = match_quality(user, scholarship)
        major = next(c for c in result["components"] if c["name"] == "Major alignment")
        assert major["score"] == 100.0

    def test_major_soft_mismatch_scores_zero_not_hidden(self):
        """This is the fix for the old exact-match eligibility bug: a
        mismatch still ranks (score 0), it doesn't disappear."""
        user = make_user(major="fine arts")
        scholarship = make_scholarship(majors=["computer science"], majors_are_hard_requirement=False)
        result = match_quality(user, scholarship)
        major = next(c for c in result["components"] if c["name"] == "Major alignment")
        assert major["score"] == 0.0

    def test_major_open_to_all_scores_neutral(self):
        user = make_user()
        scholarship = make_scholarship(majors=[])
        result = match_quality(user, scholarship)
        major = next(c for c in result["components"] if c["name"] == "Major alignment")
        assert major["score"] == 50.0

    def test_interest_full_overlap_scores_100(self):
        user = make_user(interests=["stem", "coding"])
        scholarship = make_scholarship(interests=["stem", "coding"])
        result = match_quality(user, scholarship)
        interest = next(c for c in result["components"] if c["name"] == "Interest alignment")
        assert interest["score"] == 100.0

    def test_interest_zero_overlap_scores_zero(self):
        user = make_user(interests=["business"])
        scholarship = make_scholarship(interests=["stem", "coding"])
        result = match_quality(user, scholarship)
        interest = next(c for c in result["components"] if c["name"] == "Interest alignment")
        assert interest["score"] == 0.0

    def test_interest_partial_overlap_is_proportional(self):
        user = make_user(interests=["stem"])
        scholarship = make_scholarship(interests=["stem", "coding", "robotics", "art"])
        result = match_quality(user, scholarship)
        interest = next(c for c in result["components"] if c["name"] == "Interest alignment")
        assert interest["score"] == 25.0  # 1 of 4

    def test_sparse_criteria_scholarship_does_not_inflate_score(self):
        """The core Layer 2 bug fix: a scholarship with almost no listed
        criteria should NOT be able to out-score a scholarship that
        genuinely matches on GPA, major, and interests, just because it
        has fewer components to clear. This directly re-creates the
        comparison from the architecture review."""
        user = make_user(gpa=3.6, major="computer science", interests=["stem", "coding", "robotics"])

        sparse = make_scholarship(min_gpa=None, majors=[], interests=[])  # nothing restricts it
        strong_real_match = make_scholarship(
            min_gpa=3.0, majors=["computer science"], majors_are_hard_requirement=False,
            interests=["stem", "robotics"],
        )

        sparse_score = match_quality(user, sparse)["score"]
        real_match_score = match_quality(user, strong_real_match)["score"]
        assert real_match_score > sparse_score

    def test_labels_follow_fixed_absolute_bands(self):
        assert match_quality(make_user(gpa=4.0), make_scholarship(min_gpa=3.0, majors=["computer science"], interests=["stem"]))["label"] in (
            "Excellent fit", "Strong fit"
        )


# ---------------------------------------------------------------------------
# Layer 3: Competitiveness estimate + raw application value
# ---------------------------------------------------------------------------

class TestCompetitivenessAndValue:
    def test_ratio_is_awards_over_pool(self):
        scholarship = make_scholarship(num_awards=5, estimated_applicant_pool=1000)
        result = competitiveness_estimate(scholarship)
        assert result["ratio"] == 0.005
        assert result["one_in"] == 200

    def test_never_returns_a_percent_or_probability_key(self):
        """Guards against regression back into calling this a probability
        anywhere in the payload."""
        scholarship = make_scholarship()
        result = competitiveness_estimate(scholarship)
        assert "probability" not in result
        assert "chance_of_winning" not in result
        assert "percent" not in "".join(result.keys())

    def test_pool_smaller_than_awards_is_floored_not_over_100_percent(self):
        scholarship = make_scholarship(num_awards=50, estimated_applicant_pool=10)
        result = competitiveness_estimate(scholarship)
        assert result["ratio"] <= 1.0

    def test_dollars_per_hour_is_amount_over_hours(self):
        user = make_user()
        scholarship = make_scholarship(award_amount=1000, estimated_hours_to_apply=4)
        scores = calculate_scores(user, scholarship)
        assert scores["application_value_raw"]["dollars_per_hour_if_won"] == 250.0

    def test_expected_value_uses_competitiveness_ratio(self):
        user = make_user()
        scholarship = make_scholarship(award_amount=1000, num_awards=1, estimated_applicant_pool=100)
        scores = calculate_scores(user, scholarship)
        assert scores["application_value_raw"]["expected_value"] == 10.0  # 1000 * (1/100)


# ---------------------------------------------------------------------------
# Urgency -- must never touch value
# ---------------------------------------------------------------------------

class TestUrgency:
    TODAY = date(2026, 9, 1)

    def test_no_deadline_is_normal(self):
        result = urgency_classification(None, today=self.TODAY)
        assert result == {"class": "normal", "days_left": None}

    def test_boundary_3_days_is_critical(self):
        assert urgency_classification(self.TODAY + timedelta(days=3), today=self.TODAY)["class"] == "critical"

    def test_boundary_4_days_is_urgent(self):
        assert urgency_classification(self.TODAY + timedelta(days=4), today=self.TODAY)["class"] == "urgent"

    def test_boundary_14_days_is_urgent(self):
        assert urgency_classification(self.TODAY + timedelta(days=14), today=self.TODAY)["class"] == "urgent"

    def test_boundary_15_days_is_approaching(self):
        assert urgency_classification(self.TODAY + timedelta(days=15), today=self.TODAY)["class"] == "approaching"

    def test_boundary_30_days_is_approaching(self):
        assert urgency_classification(self.TODAY + timedelta(days=30), today=self.TODAY)["class"] == "approaching"

    def test_boundary_31_days_is_normal(self):
        assert urgency_classification(self.TODAY + timedelta(days=31), today=self.TODAY)["class"] == "normal"

    def test_past_deadline_is_critical_not_an_error(self):
        assert urgency_classification(self.TODAY - timedelta(days=5), today=self.TODAY)["class"] == "critical"

    def test_urgency_never_appears_inside_application_value(self):
        """Structural guard for the explicit design requirement: urgency
        must be a sibling of application value, never folded into it."""
        user = make_user()
        scholarship = make_scholarship(deadline=date(2026, 9, 2))  # 1 day out
        scores = calculate_scores(user, scholarship, today=self.TODAY)
        assert "urgency" not in scores["application_value_raw"]
        # And the raw dollar figures for a 1-day-out deadline must be
        # identical to the same scholarship with no deadline at all.
        no_deadline_version = make_scholarship(deadline=None)
        scores_no_deadline = calculate_scores(user, no_deadline_version, today=self.TODAY)
        assert scores["application_value_raw"] == scores_no_deadline["application_value_raw"]


# ---------------------------------------------------------------------------
# calculate_scores() bundle behavior
# ---------------------------------------------------------------------------

class TestCalculateScoresBundle:
    def test_ineligible_scholarship_has_no_match_quality_or_value(self):
        user = make_user(gpa=1.0)
        scholarship = make_scholarship(min_gpa=3.5)
        scores = calculate_scores(user, scholarship)
        assert scores["eligible"] is False
        assert scores["match_quality"] is None
        assert scores["competitiveness"] is None
        assert scores["application_value_raw"] is None
        assert scores["ineligible_reasons"] != []

    def test_ineligible_scholarship_still_gets_urgency(self):
        """Urgency is a calendar fact independent of eligibility -- a
        saved item that's become ineligible should still show its
        deadline urgency in the UI."""
        user = make_user(gpa=1.0)
        scholarship = make_scholarship(min_gpa=3.5, deadline=date(2026, 9, 2))
        scores = calculate_scores(user, scholarship, today=date(2026, 9, 1))
        assert scores["urgency"]["class"] == "critical"

    def test_eligible_scholarship_has_all_layers(self):
        user = make_user()
        scholarship = make_scholarship()
        scores = calculate_scores(user, scholarship)
        assert scores["eligible"] is True
        assert scores["match_quality"] is not None
        assert scores["competitiveness"] is not None
        assert scores["application_value_raw"] is not None
