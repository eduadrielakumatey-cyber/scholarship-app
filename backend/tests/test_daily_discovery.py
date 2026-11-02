"""
tests/test_daily_discovery.py
---------------------------------
The daily 5am run inserts scholarships with no human review, so every
safety check in scraper/daily_discovery.py gets a test that tries to sneak
a bad listing past it. All pure -- no network, no database.

Run with:
    cd backend
    pytest tests/test_daily_discovery.py
"""

from datetime import date

import pytest

from scraper.daily_discovery import (
    ExistingIndex,
    MAX_DAYS_TO_DEADLINE,
    _same_site,
    amount_variants,
    deadline_variants,
    fee_red_flag,
    normalize_text,
    title_on_page,
    validate_fields,
    verify_page_content,
)

TODAY = date(2026, 11, 2)


def good_candidate(**overrides):
    c = {
        "title": "Rivera Family STEM Scholarship",
        "organization": "Rivera Community Foundation",
        "source_url": "https://www.riverafoundation.org/scholarships/stem",
        "description": "Supports high school seniors planning to study a STEM field at an accredited college.",
        "amount": 5000,
        "deadline": "2027-03-15",
        "grade_levels": ["12"],
        "states": ["TX"],
        "demographics": [],
        "majors": ["engineering"],
        "interests": ["stem"],
        "min_gpa": 3.0,
        "award_frequency": "one_time",
        "num_awards": 4,
        "evidence": "Four awards of $5,000 each will be given to graduating seniors.",
    }
    c.update(overrides)
    return c


GOOD_PAGE = """
<nav>Home | About | Donate</nav>
The Rivera Family STEM Scholarship supports Texas high school seniors.
Four awards of $5,000 each will be given to graduating seniors.
Applications are due March 15, 2027. There is no application fee.
Eligibility: minimum 3.0 GPA, planning to study engineering, math or science.
""" * 2


# --- Field checks -----------------------------------------------------------

def test_good_candidate_passes_field_checks():
    assert validate_fields(good_candidate(), TODAY) == []


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"amount": 50}, "outside"),
        ({"amount": 5_000_000}, "outside"),
        ({"amount": "5000"}, "must be a number"),
        ({"amount": True}, "must be a number"),
        ({"deadline": "2026-10-01"}, "has passed"),
        ({"deadline": "2026-11-03"}, "under"),
        ({"deadline": "2029-01-01"}, "implausibly far"),
        ({"deadline": "March 15"}, "YYYY-MM-DD"),
        ({"deadline": None}, "not marked rolling"),
        ({"source_url": "http://riverafoundation.org/x"}, "https"),
        ({"source_url": "https://www.fastweb.com/college-scholarships/123"}, "aggregator"),
        ({"source_url": "https://scholarships.bold.org/rivera"}, "aggregator"),
        ({"source_url": "https://bit.ly/abc123"}, "aggregator"),
        ({"source_url": "https://riverafoundation.org/flyer.pdf"}, "PDF"),
        ({"grade_levels": []}, "grade_levels"),
        ({"grade_levels": ["11"]}, "unknown grade level"),
        ({"states": ["Texas"]}, "invalid state"),
        ({"demographics": ["gamer"]}, "unknown demographic"),
        ({"min_gpa": 7}, "min_gpa"),
        ({"award_frequency": "monthly"}, "award_frequency"),
        ({"num_awards": 0}, "num_awards"),
        ({"evidence": ""}, "evidence"),
        ({"description": "Short."}, "description"),
        ({"title": ""}, "title"),
    ],
)
def test_bad_fields_are_rejected(overrides, expected):
    problems = validate_fields(good_candidate(**overrides), TODAY)
    assert any(expected in p for p in problems), problems


def test_rolling_scholarship_without_deadline_is_allowed():
    assert validate_fields(good_candidate(deadline=None, rolling=True), TODAY) == []


def test_deadline_window_edges():
    assert validate_fields(good_candidate(deadline="2026-11-05"), TODAY) == []
    far = date.fromordinal(TODAY.toordinal() + MAX_DAYS_TO_DEADLINE).isoformat()
    assert validate_fields(good_candidate(deadline=far), TODAY) == []


# --- Page proof -------------------------------------------------------------

def test_good_page_verifies():
    assert verify_page_content(good_candidate(), GOOD_PAGE) == []


def test_wrong_amount_is_caught():
    problems = verify_page_content(good_candidate(amount=10000), GOOD_PAGE)
    assert any("amount" in p for p in problems)


def test_amount_is_not_matched_inside_a_bigger_number():
    page = GOOD_PAGE.replace("$5,000", "$15,000")
    problems = verify_page_content(good_candidate(evidence="Applications are due March 15, 2027."), page)
    assert any("amount" in p for p in problems)


def test_wrong_deadline_is_caught():
    problems = verify_page_content(good_candidate(deadline="2027-04-15"), GOOD_PAGE)
    assert any("deadline" in p for p in problems)


@pytest.mark.parametrize(
    "written",
    ["March 15, 2027", "Mar. 15", "march 15th", "15 March 2027", "3/15/2027", "03/15/2027", "2027-03-15"],
)
def test_deadline_formats_are_recognized(written):
    page = normalize_text(f"Deadline: {written}. " + "filler text " * 30)
    variants = deadline_variants(date(2027, 3, 15))
    assert any(v in page for v in variants), (written, variants)


def test_made_up_scholarship_name_is_caught():
    problems = verify_page_content(good_candidate(title="Hernandez Robotics Award"), GOOD_PAGE)
    assert any("name not found" in p for p in problems)


def test_paraphrased_evidence_is_caught():
    problems = verify_page_content(good_candidate(evidence="They give out several $5,000 prizes to seniors."), GOOD_PAGE)
    assert any("evidence" in p for p in problems)


def test_application_fee_is_caught():
    page = GOOD_PAGE.replace("There is no application fee.", "A $25 application fee is required.")
    problems = verify_page_content(good_candidate(), page)
    assert any("fee" in p for p in problems)


@pytest.mark.parametrize(
    "text, flagged",
    [
        ("there is no application fee", False),
        ("applying is free; no processing fee", False),
        ("we will never charge an application fee", False),
        ("a $30 processing fee applies", True),
        ("you must pay to apply", True),
    ],
)
def test_fee_negation_handling(text, flagged):
    assert (fee_red_flag(text) is not None) == flagged


def test_blank_or_js_only_page_is_rejected():
    problems = verify_page_content(good_candidate(), "<div id='root'></div>")
    assert any("almost no readable text" in p for p in problems)


def test_amount_variants():
    assert "5 000" in amount_variants(5000)
    assert "5k" in amount_variants(5000)
    assert "2 500" in amount_variants(2500)


def test_title_matching_ignores_generic_words():
    page = normalize_text("Apply for the Rivera Family STEM award today " * 10)
    assert title_on_page("Rivera Family STEM Scholarship Program", page)
    assert not title_on_page("Okafor Nursing Scholarship", page)


# --- Redirects & dedupe -----------------------------------------------------

def test_same_site_allows_subdomains_but_not_other_sites():
    assert _same_site("https://www.example.org/a", "https://apply.example.org/b")
    assert not _same_site("https://example.org/a", "https://hugedomains.com/domain/example.org")


def test_duplicates_are_detected_three_ways():
    index = ExistingIndex()
    index.add("Rivera Family STEM Scholarship", "Rivera Community Foundation", "https://riverafoundation.org/stem/")
    assert index.duplicate_reason("Rivera Family STEM Scholarship", "Rivera Community Foundation", "https://x.org") == "same title and organization"
    assert index.duplicate_reason("Totally Different", "Other Org", "https://www.riverafoundation.org/stem") == "same official URL"
    assert "near-identical" in index.duplicate_reason("Rivera Family STEM Scholarships", "Rivera Community Foundation", "https://y.org")
    assert index.duplicate_reason("Rivera Arts Scholarship", "Rivera Community Foundation", "https://z.org") is None


def test_same_program_under_a_different_org_name_is_a_duplicate():
    # Real case: the database had "Ron Brown Scholar Program" filed under
    # "Ron Brown Scholar Fund"; research found it as "... Program".
    index = ExistingIndex()
    index.add("Ron Brown Scholar Program", "Ron Brown Scholar Fund", "https://www.ronbrown.org/")
    assert index.duplicate_reason(
        "Ron Brown Scholar Program", "Ron Brown Scholar Program", "https://ronbrown.org/ron-brown-scholarship/"
    ) is not None
    assert index.duplicate_reason(
        "Ron Brown Signature Scholarship", "RBSP", "https://ronbrown.org/ron-brown-scholarship/"
    ) is not None


def test_separate_awards_from_one_foundation_are_not_duplicates():
    index = ExistingIndex()
    index.add("Coolidge Scholarship", "Calvin Coolidge Presidential Foundation", "https://coolidgescholars.org/")
    assert index.duplicate_reason(
        "Coolidge Senator John Heinz Scholarship", "Calvin Coolidge Foundation", "https://coolidgescholars.org/heinz"
    ) is None


# ---------------------------------------------------------------------------
# JavaScript-rendered pages
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, html):
        self.text = html
        self.status_code = 200
        self.url = "https://grants.example.gov/award"
        self.headers = {"Content-Type": "text/html"}


RENDERED = "Example State Grant awards up to $2,000 per year to residents. " * 10


def test_js_only_page_is_rerendered(monkeypatch):
    import scraper.daily_discovery as dd

    monkeypatch.setattr(dd.requests, "get", lambda *a, **k: _FakeResponse("<div id=app></div>"))
    monkeypatch.setattr(dd, "render_page", lambda url: (RENDERED, url))
    text, final_url, err = dd.fetch_page("https://grants.example.gov/award")
    assert err == "" and "$2,000" in text and final_url == "https://grants.example.gov/award"


def test_plain_page_skips_the_browser(monkeypatch):
    import scraper.daily_discovery as dd

    def boom(url):
        raise AssertionError("browser should not run for a readable page")

    monkeypatch.setattr(dd.requests, "get", lambda *a, **k: _FakeResponse(f"<p>{RENDERED}</p>"))
    monkeypatch.setattr(dd, "render_page", boom)
    text, _, err = dd.fetch_page("https://grants.example.gov/award")
    assert err == "" and "$2,000" in text


def test_failed_render_keeps_the_empty_page(monkeypatch):
    import scraper.daily_discovery as dd

    monkeypatch.setattr(dd.requests, "get", lambda *a, **k: _FakeResponse("<div id=app></div>"))
    monkeypatch.setattr(dd, "render_page", lambda url: (None, url))
    text, _, _ = dd.fetch_page("https://grants.example.gov/award")
    assert verify_page_content({"title": "x", "amount": 500}, text)[0].startswith("official page has almost no readable text")
