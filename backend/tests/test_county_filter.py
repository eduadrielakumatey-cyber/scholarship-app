"""
tests/test_county_filter.py
-----------------------------
County awards (e.g. a county foundation's) are shown only to students who
live in that county; students who haven't said where they live don't see
them yet. DB-free, like the rest of the suite.

    pytest tests/test_county_filter.py
"""

from datetime import date
from types import SimpleNamespace

from app.services.matching import _reason_category
from app.services.scoring import is_eligible, matched_on
from app.utils.validators import MD_COUNTIES, is_valid_county
from scraper.daily_discovery import school_for, validate_fields
from tests.test_daily_discovery import good_candidate


def user(**kw):
    base = dict(gpa=3.5, grade_level="12", state="MD", demographics=[], interests=[], major="biology",
                schools=None, county=None)
    base.update(kw)
    return SimpleNamespace(**base)


def award(**kw):
    base = dict(min_gpa=None, grade_levels=["12"], states=["MD"], demographics=[], majors=[],
                majors_are_hard_requirement=False, interests=[], school=None, counties=[])
    base.update(kw)
    return SimpleNamespace(**base)


def test_any_county_award_is_shown_to_everyone():
    assert is_eligible(user(), award())[0]
    assert is_eligible(user(county="Howard"), award())[0]


def test_county_award_shown_to_that_county():
    ok, _ = is_eligible(user(county="Carroll"), award(counties=["Carroll"]))
    assert ok
    assert "County: Carroll County" in matched_on(user(county="Carroll"), award(counties=["Carroll"]))


def test_county_award_hidden_from_other_counties():
    ok, reasons = is_eligible(user(county="Howard"), award(counties=["Carroll"]))
    assert not ok and reasons == ["Only for students in Carroll County"]
    assert _reason_category(reasons[0]) == "Only for students in other counties"


def test_county_award_hidden_until_student_picks_a_county():
    ok, reasons = is_eligible(user(county=None), award(counties=["Carroll"]))
    assert not ok
    assert _reason_category(reasons[0]) == "Local awards (add your county to see them)"


def test_multi_county_and_city_labels():
    _, reasons = is_eligible(user(county="Kent"), award(counties=["Baltimore City", "Howard"]))
    assert reasons == ["Only for students in Baltimore City or Howard County"]


def test_county_list():
    assert len(MD_COUNTIES) == 24
    assert is_valid_county("Prince George's") and not is_valid_county("Howard County")


def test_discovery_accepts_counties_only_for_maryland():
    today = date(2026, 11, 22)
    assert validate_fields(good_candidate(states=["MD"], counties=["Carroll"]), today) == []
    assert any("unknown Maryland county" in p for p in validate_fields(good_candidate(states=["MD"], counties=["Narnia"]), today))
    assert any("states must be exactly" in p for p in validate_fields(good_candidate(states=[], counties=["Carroll"]), today))


def test_foundation_portal_is_not_a_college():
    c = {"source_url": "https://somefoundation.academicworks.com/opportunities/1", "organization": "Some Foundation"}
    assert school_for(c) == "Some Foundation"
    assert school_for({**c, "school": False}) is None
