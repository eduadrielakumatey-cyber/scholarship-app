"""
scraper/daily_discovery.py
------------------------------
The insertion gate for the daily 5am discovery run. Research (finding
candidate scholarships on the web) happens upstream and drops a JSON list
of candidates into discovery_inbox/<date>.json; this module decides, with
no human in the loop, which of them are safe to show students.

The bar is "prove it, or it doesn't go in". A candidate is inserted only
if it passes ALL of:

  1. Field checks    -- required fields present and sane (amount range,
                        future deadline or explicit rolling, valid grade
                        levels/states/demographics, https official link,
                        not an aggregator/lead-gen site, not a PDF).
  2. Dedupe          -- not already in the database (normalized title+org,
                        same official URL, or a near-identical title from
                        the same organization), and not repeated in the batch.
  3. Link check      -- scraper.link_checker.check_url says "active" (the
                        same function the weekly freshness job uses).
  4. Page proof      -- the official page itself, fetched fresh, must
                        contain the scholarship's name, the award amount,
                        the deadline date (if one is claimed) and the
                        verbatim evidence quote, must not redirect to a
                        different site, and must not ask for an
                        application/processing fee. This is what stops a
                        wrong amount, made-up deadline or scam listing.
                        Pages that render their text with JavaScript are
                        re-read in headless Chromium (if Playwright is
                        installed); the same checks apply to that text.
  5. Run cap         -- at most MAX_INSERTS_PER_RUN per run (raise it with
                        --max for a one-off backfill), so a bad daily run
                        can't flood the deck.

Accepted rows are inserted in ONE transaction, then re-read and run through
the real scoring code as a smoke test; if anything fails the whole batch is
rolled back. Every run writes a report to discovery_reports/<date>.md
listing what was added and exactly why anything was rejected.

Each day's rows share source_name="daily_discovery_<YYYY_MM_DD>", so a
whole day can be pulled with --undo (soft: deactivated, not deleted, so
students' saved items never break).

Usage:
    python -m scraper.daily_discovery discovery_inbox/2026-11-02.json
    python -m scraper.daily_discovery discovery_inbox/2026-11-02.json --dry-run
    python -m scraper.daily_discovery discovery_inbox/backfill-states.json --max 200 --label state-grants
    python -m scraper.daily_discovery --undo 2026-11-02
"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from scraper.dedupe import _normalize_url
from scraper.link_checker import (
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
    check_url,
)
from app.utils.validators import GRADE_LEVEL_CODES, US_STATE_CODES, normalize_interests

logger = logging.getLogger("daily_discovery")

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BACKEND_DIR / "discovery_reports"

MAX_INSERTS_PER_RUN = 40
MIN_AMOUNT = 250
MAX_AMOUNT = 300_000
MIN_DAYS_TO_DEADLINE = 3      # not worth showing something due in two days
MAX_DAYS_TO_DEADLINE = 450    # further out than this is almost always a misread year

# Must match the demographic chips students can pick (ProfileSetup.jsx);
# a tag outside this list could never match anyone.
ALLOWED_DEMOGRAPHICS = {
    "first-generation", "female", "male", "veteran", "rural", "lgbtq+",
    "hispanic", "black", "asian", "native-american", "disability",
}
ALLOWED_FREQUENCIES = {"one_time", "annual", "unknown"}

# Aggregators and lead-generation "scholarship" sites: we only list the
# provider's own official page, never a middleman's copy of it.
BLOCKED_DOMAINS = {
    "fastweb.com", "scholarships.com", "niche.com", "bold.org", "unigo.com",
    "scholarshipowl.com", "cappex.com", "chegg.com", "scholarships360.org",
    "goingmerry.com", "collegexpress.com", "petersons.com", "raise.me",
    "scholarshipportal.com", "collegescholarships.org", "careeronestop.org",
    "bigfuture.collegeboard.org", "studentscholarships.org", "scholarshiproar.com",
    "bit.ly", "tinyurl.com", "t.co", "forms.gle", "docs.google.com",
}

# Platforms where each subdomain is a different school or foundation.
MULTI_TENANT_PORTALS = {"academicworks.com", "smarterselect.com", "communityforce.com", "awardspring.com"}

# Words that don't help tell one scholarship's name from another's.
TITLE_STOPWORDS = {
    "the", "and", "for", "of", "in", "a", "an", "to", "scholarship", "scholarships", "scholar", "scholars",
    "award", "awards", "program", "programs", "fund", "foundation", "grant", "grants",
    "annual", "student", "students", "memorial",
}

FEE_PATTERN = re.compile(r"(application|processing|entry|registration|submission|handling)\s+fee|pay to apply")
FEE_NEGATIONS = ("no ", "not ", "free", "without", "waive", "never", "there is no", "n't")

MONTHS = [
    ("january", "jan"), ("february", "feb"), ("march", "mar"), ("april", "apr"),
    ("may", "may"), ("june", "jun"), ("july", "jul"), ("august", "aug"),
    ("september", "sep"), ("october", "oct"), ("november", "nov"), ("december", "dec"),
]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def normalize_text(text: str | None) -> str:
    """Lowercase, letters/digits only, single spaces. Used for every
    'does the page contain X' comparison so punctuation/markup can't
    cause false mismatches."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9$]+", " ", (text or "").lower())).strip()


def _key(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:120]


def _host(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _is_blocked(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS)


def _same_site(a: str, b: str) -> bool:
    """True if two hosts belong to the same site (one is the other or a
    subdomain of it, e.g. apply.example.org vs example.org)."""
    a, b = _host(a), _host(b)
    if not a or not b:
        return False
    root = lambda h: ".".join(h.split(".")[-2:])  # noqa: E731
    return a == b or a.endswith("." + b) or b.endswith("." + a) or root(a) == root(b)


# An award limited to one state's residents (or one county, or one college)
# draws from a far smaller pool than a national one of the same size.
LOCAL_POOL_DIVISOR = 10


def estimate_applicant_pool(amount: float, states: list | None = None) -> int:
    # Same buckets as scraper/sources/base.py so new rows score like old ones.
    if amount < 1000:
        pool = 800
    elif amount < 5000:
        pool = 2500
    elif amount < 20000:
        pool = 4000
    else:
        pool = 6000
    if states and len(states) == 1:
        pool //= LOCAL_POOL_DIVISOR
    return pool


# ---------------------------------------------------------------------------
# 1. Field checks (pure -- no network, no DB)
# ---------------------------------------------------------------------------

_PLACE = (
    r"(alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|"
    r"idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|"
    r"minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|"
    r"new york|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|"
    r"south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|"
    r"wisconsin|wyoming|dc|d\.c\.|district of columbia)"
)
_RESIDENCY = re.compile(
    rf"\b{_PLACE} residents?\b|\bresidents? of (the )?{_PLACE}\b|\b{_PLACE} high school (seniors|students|graduates)\b",
    re.IGNORECASE,
)


def residency_mentioned(description: str) -> str | None:
    """The phrase if a description limits the award to one state's residents."""
    m = _RESIDENCY.search(description or "")
    return m.group(0) if m else None


def validate_fields(c: dict, today: date) -> list[str]:
    """Returns a list of problems; empty means the candidate's fields are OK."""
    problems: list[str] = []

    title = (c.get("title") or "").strip()
    org = (c.get("organization") or "").strip()
    desc = (c.get("description") or "").strip()
    if not (4 <= len(title) <= 200):
        problems.append("title missing or wrong length")
    if not (2 <= len(org) <= 200):
        problems.append("organization missing")
    if not (40 <= len(desc) <= 1500):
        problems.append("description must be 40-1500 characters")

    url = (c.get("source_url") or "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        problems.append("source_url must be a full https:// link")
    else:
        if _is_blocked(_host(url)):
            problems.append(f"source_url is an aggregator/shortener ({_host(url)}), not the official provider")
        if parsed.path.lower().endswith(".pdf"):
            problems.append("source_url is a PDF (can't be verified automatically)")

    amount = c.get("amount")
    if c.get("amount_varies") is True:
        if amount not in (None, 0):
            problems.append("amount_varies is true, so amount must be left out")
    elif isinstance(amount, bool) or not isinstance(amount, (int, float)):
        problems.append("amount must be a number")
    elif not (MIN_AMOUNT <= amount <= MAX_AMOUNT):
        problems.append(f"amount {amount} outside ${MIN_AMOUNT:,}-${MAX_AMOUNT:,}")

    deadline_raw = c.get("deadline")
    if deadline_raw:
        try:
            deadline = datetime.strptime(str(deadline_raw), "%Y-%m-%d").date()
        except ValueError:
            problems.append("deadline must be YYYY-MM-DD")
        else:
            days = (deadline - today).days
            if days < MIN_DAYS_TO_DEADLINE:
                problems.append(f"deadline {deadline} has passed or is under {MIN_DAYS_TO_DEADLINE} days away")
            elif days > MAX_DAYS_TO_DEADLINE:
                problems.append(f"deadline {deadline} is implausibly far out (likely wrong year)")
    elif c.get("rolling") is not True:
        problems.append("no deadline given and not marked rolling")

    grades = c.get("grade_levels")
    if not isinstance(grades, list) or not grades:
        problems.append("grade_levels must list who can apply")
    elif any(g not in GRADE_LEVEL_CODES for g in grades):
        problems.append(f"unknown grade level in {grades}")

    states = c.get("states") or []
    if not isinstance(states, list) or any(str(s).upper() not in US_STATE_CODES for s in states):
        problems.append(f"invalid state code in {states}")
    elif not states:
        residency = residency_mentioned(desc)
        if residency:
            # A "national" listing whose own description says it's for one
            # place's residents would be shown to students everywhere.
            problems.append(f"states is empty but the description says '{residency}'; set states")

    demos = c.get("demographics") or []
    if not isinstance(demos, list) or any(d not in ALLOWED_DEMOGRAPHICS for d in demos):
        problems.append(f"unknown demographic tag in {demos}")

    gpa = c.get("min_gpa")
    if gpa is not None and (isinstance(gpa, bool) or not isinstance(gpa, (int, float)) or not 0 < gpa <= 5):
        problems.append("min_gpa must be between 0 and 5")

    freq = c.get("award_frequency", "unknown")
    if freq not in ALLOWED_FREQUENCIES:
        problems.append(f"award_frequency must be one of {sorted(ALLOWED_FREQUENCIES)}")

    num_awards = c.get("num_awards")
    if num_awards is not None and (isinstance(num_awards, bool) or not isinstance(num_awards, int) or not 1 <= num_awards <= 10000):
        problems.append("num_awards must be a whole number 1-10000")

    if len((c.get("evidence") or "").strip()) < 15:
        problems.append("evidence quote missing (need a verbatim line from the official page)")

    if not isinstance(c.get("essay_required"), bool):
        problems.append("essay_required must be true or false, decided from the official page")

    return problems


# ---------------------------------------------------------------------------
# 4. Page proof (pure given page text -- testable without the network)
# ---------------------------------------------------------------------------

# How AcademicWorks pages show an award with no fixed amount.
VARIES_ON_PAGE = re.compile(r"Award\s+(Varies|\$0\.00)(?![\d,])", re.I)


def amount_variants(amount: float) -> list[str]:
    n = int(round(amount))
    variants = {f"{n:,}", str(n)}
    if n % 1000 == 0:
        variants.add(f"{n // 1000}k")
    if n % 1_000_000 == 0:
        variants.add(f"{n // 1_000_000} million")
    # normalize_text turns "5,000" into "5 000" -- match that too
    return sorted({normalize_text(v) for v in variants})


def deadline_variants(d: date) -> list[str]:
    full, abbr = MONTHS[d.month - 1]
    day = str(d.day)
    suffix = "th" if 11 <= d.day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d.day % 10, "th")
    out = [
        f"{full} {day}", f"{abbr} {day}", f"{day} {full}", f"{day} {abbr}",
        f"{full} {day}{suffix}", f"{abbr} {day}{suffix}", f"{day}{suffix} {full}",
        f"{d.month} {day} {d.year}", f"{d.month:02d} {d.day:02d} {d.year}",
        f"{d.month} {day} {d.year % 100:02d}", f"{d.month:02d} {d.day:02d} {d.year % 100:02d}",
        f"{d.year} {d.month:02d} {d.day:02d}",
    ]
    return [normalize_text(v) for v in out]


def _contains_phrase(page: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", page) is not None


def _distinctive_words(title: str) -> set[str]:
    return {t for t in normalize_text(title).split() if len(t) >= 3 and t not in TITLE_STOPWORDS}


def _similar(a: str, b: str) -> float:
    """How alike two names are, ignoring filler like "Memorial Scholarship",
    so "Paul S. Andrews Memorial Scholarship" and "Charm Satree Memorial
    Scholarship" don't look alike just because they end the same way."""
    da = " ".join(t for t in normalize_text(a).split() if t not in TITLE_STOPWORDS)
    db = " ".join(t for t in normalize_text(b).split() if t not in TITLE_STOPWORDS)
    if not da or not db:
        da, db = normalize_text(a), normalize_text(b)
    return difflib.SequenceMatcher(None, da, db).ratio()


def _different_numbers(a: str, b: str) -> bool:
    """"Class of 1948" and "Class of 1962" are separate awards."""
    na, nb = set(re.findall(r"\d+", a)), set(re.findall(r"\d+", b))
    return bool(na and nb and na != nb)


def title_on_page(title: str, page: str) -> bool:
    tokens = [t for t in normalize_text(title).split() if len(t) >= 3 and t not in TITLE_STOPWORDS]
    if not tokens:
        return _contains_phrase(page, normalize_text(title))
    found = sum(1 for t in tokens if _contains_phrase(page, t))
    return found / len(tokens) >= 0.6


def fee_red_flag(page_lower: str) -> str | None:
    """Returns the offending snippet if the page asks applicants to pay."""
    for m in FEE_PATTERN.finditer(page_lower):
        before = page_lower[max(0, m.start() - 30):m.start()]
        if any(neg in before for neg in FEE_NEGATIONS):
            continue
        # "covers tuition and admission/application fees" lists a cost the
        # aid pays for, not a charge to apply for the aid.
        if before.endswith(("admission/", "admission or ", "admissions/")):
            continue
        return page_lower[max(0, m.start() - 30):m.end() + 10].strip()
    return None


# What counts as "an essay": any written response the student has to compose
# (an essay, personal statement, or a describe/explain/tell-us question).
# A one-word or yes/no question, an upload, or a reference is not one.
ESSAY_WORDS = re.compile(
    r"(?<!no )\bessays?\b|personal statement|statement of (purpose|need|goals|intent|career|financial)|"
    r"letter (explaining|describing|stating|detailing)|short answers?|written (response|statement)|"
    r"\b\d{2,4}\s*(-|to)?\s*\d{0,4}\s*words?\b|words or (less|fewer)",
    re.IGNORECASE,
)
WRITING_PROMPT = re.compile(
    r"\b(describe|explain|discuss|tell us|why do you|why are you|how will|how has|how have|"
    r"what are your|what have you|in your own words)\b",
    re.IGNORECASE,
)
NO_ESSAY = re.compile(r"no essays? (is |are )?(required|needed)|does not require an essay|without an essay", re.IGNORECASE)


def essay_mismatch(claim, page_text: str) -> str | None:
    """The problem, if the essay answer contradicts the official page.
    Students rely on the No essay / Essay required tag, so it has to be
    something the page itself supports, never a guess."""
    page = re.sub(r"\s+", " ", page_text or "")
    says_none = bool(NO_ESSAY.search(page))
    asks = bool(ESSAY_WORDS.search(page)) or bool(WRITING_PROMPT.search(page))
    if claim is True and (says_none or not asks):
        return "essay_required is true but the official page doesn't ask for an essay or written answer"
    if claim is False and ESSAY_WORDS.search(page) and not says_none:
        return "essay_required is false but the official page mentions an essay"
    return None


def page_questions(url: str, essay_required) -> list[dict]:
    """The official application's questions, word for word (see
    app/services/questions.py). [] if the page lists none or can't be read."""
    from app.services import questions as Q

    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException:
        return []
    if resp.status_code != 200:
        return []
    html = resp.content.decode("utf-8", errors="replace")
    return Q.build(html, _visible_text(html), essay_required)


_SOURCE_PAGES: dict[str, str] = {}


def general_app_essay_problem(c: dict) -> str | None:
    """For awards that are applied to through a college's General
    Application: the candidate names the college's official page
    (essay_source_url) and quotes its essay requirement word for word
    (essay_source_quote). Returns a problem, or None when proven."""
    url, quote = c.get("essay_source_url"), c.get("essay_source_quote")
    if not url:
        return None
    if c.get("essay_required") is not True:
        return "essay_source_url is only for essays required by a General Application"
    if not isinstance(quote, str) or not ESSAY_WORD.search(quote):
        return "essay_source_quote must quote the essay requirement"
    if not url.startswith("https://"):
        return "essay_source_url must be https"
    if url not in _SOURCE_PAGES:
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
            _SOURCE_PAGES[url] = resp.content.decode("utf-8", errors="replace") if resp.status_code == 200 else ""
        except requests.exceptions.RequestException:
            _SOURCE_PAGES[url] = ""
    if normalize_text(quote) not in normalize_text(_visible_text(_SOURCE_PAGES[url])):
        return "General Application essay quote not found on the college's page"
    return None


ESSAY_WORD = re.compile(r"\bessays?\b|personal statement", re.I)


def verify_page_content(c: dict, page_text: str) -> list[str]:
    """Checks the candidate's claims against the official page's text."""
    problems: list[str] = []
    page = normalize_text(page_text)
    if len(page) < 200:
        return ["official page has almost no readable text (JavaScript-only or blocked)"]

    if not title_on_page(c["title"], page):
        problems.append("scholarship name not found on the official page")

    if c.get("amount_varies") is True:
        if not VARIES_ON_PAGE.search(page):
            problems.append("amount_varies is true but the official page shows a fixed amount")
    elif not any(_contains_phrase(page, v) for v in amount_variants(c["amount"])):
        problems.append(f"award amount ${c['amount']:,} not found on the official page")

    if c.get("deadline"):
        d = datetime.strptime(c["deadline"], "%Y-%m-%d").date()
        if not any(_contains_phrase(page, v) for v in deadline_variants(d)):
            problems.append(f"deadline {c['deadline']} not found on the official page")

    evidence = normalize_text(c.get("evidence"))
    if evidence and evidence not in page:
        problems.append("evidence quote not found verbatim on the official page")

    # An essay that's part of the college's General Application is proven on
    # the college's own page (see general_app_essay_problem), not here.
    if not c.get("essay_source_url"):
        essay_problem = essay_mismatch(c.get("essay_required"), page_text)
        if essay_problem:
            problems.append(essay_problem)

    flagged = fee_red_flag(re.sub(r"\s+", " ", page_text.lower()))
    if flagged:
        problems.append(f"page mentions an applicant fee: \"{flagged}\"")

    return problems


def _visible_text(html: str) -> str:
    soup = BeautifulSoup(html[:2_000_000], "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    return soup.get_text(" ")


def render_page(url: str) -> tuple[str | None, str]:
    """Loads the page in headless Chromium and returns (visible_text, final_url).

    Only used when the plain fetch comes back nearly empty, i.e. the page
    builds its text with JavaScript. Returns (None, url) when Playwright
    isn't installed or the render fails, so the caller keeps its original
    "no readable text" rejection.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, url
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = browser.new_page(user_agent=USER_AGENT)
                page.goto(url, timeout=REQUEST_TIMEOUT_SECONDS * 2000, wait_until="networkidle")
                return _visible_text(page.content()), page.url
            finally:
                browser.close()
    except Exception as exc:  # any browser failure just means "couldn't render"
        logger.info("render failed for %s: %s", url, exc.__class__.__name__)
        return None, url


def fetch_page(url: str) -> tuple[str | None, str, str]:
    """Returns (visible_text or None, final_url, error)."""
    try:
        resp = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=True
        )
    except requests.exceptions.RequestException as exc:
        return None, url, f"could not fetch page: {exc.__class__.__name__}"
    if not 200 <= resp.status_code < 300:
        return None, resp.url, f"HTTP {resp.status_code} when fetching page"
    if "html" not in resp.headers.get("Content-Type", "html"):
        return None, resp.url, "page is not HTML"
    text = _visible_text(resp.text)
    if len(normalize_text(text)) < 200:
        rendered, rendered_url = render_page(resp.url)
        if rendered and len(normalize_text(rendered)) > len(normalize_text(text)):
            return rendered, rendered_url, ""
    return text, resp.url, ""


# ---------------------------------------------------------------------------
# 2. Dedupe
# ---------------------------------------------------------------------------

@dataclass
class ExistingIndex:
    keys: set = field(default_factory=set)             # (title_key, org_key)
    title_keys: set = field(default_factory=set)       # title_key alone
    urls: set = field(default_factory=set)             # normalized URLs
    titles_by_org: dict = field(default_factory=dict)  # org_key -> [normalized titles]
    titles_by_site: dict = field(default_factory=dict) # site -> [normalized titles]

    @staticmethod
    def _site(url: str | None) -> str:
        host = _host(url or "")
        if not host:
            return ""
        domain = ".".join(host.split(".")[-2:])
        # Shared portals host many unrelated schools and foundations, one per
        # subdomain (allegany.academicworks.com, csmd.academicworks.com), so
        # each subdomain counts as its own website.
        return host if domain in MULTI_TENANT_PORTALS else domain

    def add(self, title: str, org: str | None, url: str | None) -> None:
        self.keys.add((_key(title), _key(org)))
        self.title_keys.add(_key(title))
        norm = _normalize_url(url)
        if norm:
            self.urls.add(norm)
        t = normalize_text(title)
        self.titles_by_org.setdefault(_key(org), []).append(t)
        if self._site(url):
            self.titles_by_site.setdefault(self._site(url), []).append(t)

    def duplicate_reason(self, title: str, org: str | None, url: str | None) -> str | None:
        if (_key(title), _key(org)) in self.keys:
            return "same title and organization"
        # The same program is often recorded under slightly different
        # organization names ("Ron Brown Scholar Fund" vs "Ron Brown
        # Scholar Program"), so an identical title is a duplicate no
        # matter what the organization field says.
        if _key(title) in self.title_keys:
            return "same title (organization named differently)"
        norm = _normalize_url(url)
        if norm and norm in self.urls:
            return "same official URL"
        t = normalize_text(title)
        for other in self.titles_by_org.get(_key(org), []):
            if _different_numbers(t, other):
                continue
            if _similar(t, other) >= 0.85:
                return f"near-identical title from same organization (\"{other}\")"
        # Same website: similar wording, or one name's distinctive words all
        # appear in the other's ("Ron Brown Scholar Program" vs "Ron Brown
        # Signature Scholarship"). Needs 2+ shared distinctive words, so a
        # foundation's genuinely separate awards ("Coolidge Scholarship" vs
        # "Coolidge Senator John Heinz Scholarship") stay distinct.
        mine = _distinctive_words(t)
        for other in self.titles_by_site.get(self._site(url), []):
            if _different_numbers(t, other):
                continue
            if _similar(t, other) >= 0.75:
                return f"similar title on the same website (\"{other}\")"
            theirs = _distinctive_words(other)
            small, big = sorted((mine, theirs), key=len)
            if len(small) >= 2 and small <= big:
                return f"same program name on the same website (\"{other}\")"
        return None


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

@dataclass
class Outcome:
    candidate: dict
    accepted: bool = False
    reasons: list = field(default_factory=list)
    duplicate: str | None = None
    scholarship_id: int | None = None


def school_for(c: dict) -> str | None:
    """The one college a winner must attend, or None for any school. An
    explicit "school" on the candidate wins; otherwise every award on a
    college's own AcademicWorks portal belongs to that college."""
    if isinstance(c.get("school"), str) and c["school"].strip():
        return c["school"].strip()[:160]
    host = urlparse(c.get("source_url") or "").netloc.lower()
    if host.endswith(".academicworks.com"):
        return (c.get("organization") or "").strip()[:160] or None
    return None


def _build_row(c: dict, batch_source: str, today: date):
    from app.models import Scholarship

    varies = c.get("amount_varies") is True
    amount = 0.0 if varies else float(c["amount"])
    hours = c.get("estimated_hours_to_apply")
    hours = float(hours) if isinstance(hours, (int, float)) and 0.25 <= hours <= 60 else 2.0
    return Scholarship(
        title=c["title"].strip(),
        organization=c["organization"].strip(),
        description=c["description"].strip(),
        award_amount=amount,
        amount_varies=varies,
        award_frequency=c.get("award_frequency", "unknown"),
        renewable=c.get("renewable") if isinstance(c.get("renewable"), bool) else None,
        deadline=datetime.strptime(c["deadline"], "%Y-%m-%d").date() if c.get("deadline") else None,
        min_gpa=c.get("min_gpa"),
        grade_levels=list(c["grade_levels"]),
        states=[s.upper() for s in (c.get("states") or [])],
        demographics=list(c.get("demographics") or []),
        majors=[m.strip().lower() for m in (c.get("majors") or []) if m and m.strip()],
        interests=normalize_interests(c.get("interests") or []),
        estimated_hours_to_apply=hours,
        essay_required=c["essay_required"],
        school=school_for(c),
        questions=c.get("_questions") or [],
        estimated_applicant_pool=estimate_applicant_pool(amount or 1000.0, c.get("states")),
        num_awards=c.get("num_awards") or 1,
        source_name=batch_source,
        source_url=c["source_url"].strip(),
        external_id=f"{today.isoformat()}-{_slug(c['title'])}",
        is_active=True,
        status="active",
        last_verified_at=datetime.utcnow(),
        is_recurring_program=None,
    )


def _smoke_test(rows, today: date) -> None:
    """Runs every new row through the real eligibility/scoring code with a
    sample student, and confirms it's visible to the deck query. Raises on
    any failure so the caller can roll back."""
    from app.services.matching import _active_not_expired_query
    from app.services.scoring import calculate_scores

    student = SimpleNamespace(
        id=0, gpa=3.5, grade_level="12", state="CA", major="biology",
        interests=["stem", "community service"], demographics=[],
    )
    visible = {s.id for s in _active_not_expired_query(today).filter(
        type(rows[0]).id.in_([r.id for r in rows])
    )}
    for row in rows:
        if row.id not in visible:
            raise RuntimeError(f"inserted row {row.id} ({row.title!r}) is not visible to the deck query")
        calculate_scores(student, row, today=today)


def run(
    inbox_path: Path,
    dry_run: bool = False,
    today: date | None = None,
    delay: float = REQUEST_DELAY_SECONDS,
    max_inserts: int = MAX_INSERTS_PER_RUN,
    label: str | None = None,
) -> dict:
    from app import create_app
    from app.extensions import db
    from app.models import Scholarship

    today = today or date.today()
    batch_source = f"daily_discovery_{today.strftime('%Y_%m_%d')}"

    try:
        candidates = json.loads(Path(inbox_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read candidates file {inbox_path}: {exc}")
    if not isinstance(candidates, list):
        raise SystemExit("Candidates file must contain a JSON list")

    app = create_app("development")
    outcomes: list[Outcome] = []
    with app.app_context():
        index = ExistingIndex()
        for s in Scholarship.query.with_entities(Scholarship.title, Scholarship.organization, Scholarship.source_url):
            index.add(s.title, s.organization, s.source_url)
        # Checking every page can take many minutes, and hosted Postgres
        # (Neon) drops connections that sit idle that long. End the read
        # transaction and drop pooled connections now, so the insert at the
        # end starts on a fresh one.
        db.session.rollback()
        db.session.close()
        db.engine.dispose()

        accepted: list[Outcome] = []
        for raw in candidates:
            o = Outcome(candidate=raw if isinstance(raw, dict) else {"title": str(raw)})
            outcomes.append(o)
            c = o.candidate

            o.reasons = validate_fields(c, today)
            focus = app.config.get("FOCUS_STATE")
            if focus and focus not in [str(x).upper() for x in (c.get("states") or [])]:
                o.reasons.append(f"not limited to {focus} students; the app only shows {focus} scholarships right now")
            if o.reasons:
                continue

            o.duplicate = index.duplicate_reason(c["title"], c["organization"], c["source_url"])
            if o.duplicate:
                continue

            if len(accepted) >= max_inserts:
                o.reasons = [f"run cap of {max_inserts} reached; will be picked up another day"]
                continue

            status, detail = check_url(c["source_url"])
            time.sleep(delay)
            if status != "active":
                o.reasons = [f"link check: {status} ({detail[:120]})"]
                continue

            text, final_url, err = fetch_page(c["source_url"])
            time.sleep(delay)
            if text is None:
                o.reasons = [err]
                continue
            if not _same_site(c["source_url"], final_url):
                o.reasons = [f"link redirects to a different site ({_host(final_url)})"]
                continue

            o.reasons = verify_page_content(c, text)
            essay_source_problem = general_app_essay_problem(c)
            if essay_source_problem:
                o.reasons.append(essay_source_problem)
            if o.reasons:
                continue

            # Copy the application's questions so students can answer them
            # in the app. An essay listing must have its essay question.
            questions = page_questions(c["source_url"], c.get("essay_required"))
            if c.get("essay_source_url") and not any(q["kind"] == "written" for q in questions):
                from app.services.questions import question_key

                text_q = f"General Application essay: {c['essay_source_quote'].strip()}"
                questions.append({"key": question_key(text_q), "text": text_q, "kind": "written", "source": "general_application"})
            if c.get("essay_required") and not any(q["kind"] == "written" for q in questions):
                o.reasons = ["essay_required is true but the essay question couldn't be found on the official page"]
                continue
            c["_questions"] = questions

            o.accepted = True
            accepted.append(o)
            # Count it as "existing" so a later candidate in this batch
            # describing the same scholarship is caught as a duplicate.
            index.add(c["title"], c["organization"], c["source_url"])

        inserted_ids: list[int] = []
        db_error = None
        if accepted and not dry_run:
            try:
                rows = [_build_row(o.candidate, batch_source, today) for o in accepted]
                db.session.add_all(rows)
                db.session.flush()
                _smoke_test(rows, today)
                db.session.commit()
                for o, row in zip(accepted, rows):
                    o.scholarship_id = row.id
                    inserted_ids.append(row.id)
                # Belt and braces: re-read from the database after commit.
                stored = Scholarship.query.filter(Scholarship.id.in_(inserted_ids)).count()
                if stored != len(inserted_ids):
                    raise RuntimeError(f"expected {len(inserted_ids)} rows after commit, found {stored}")
            except Exception as exc:  # roll back the WHOLE batch on any failure
                db.session.rollback()
                db_error = f"{exc.__class__.__name__}: {exc}"
                logger.exception("Insert failed; batch rolled back")
                for o in accepted:
                    o.accepted = False
                    o.scholarship_id = None
                    o.reasons = [f"not inserted: batch rolled back ({db_error})"]
                inserted_ids = []

        total_live = None
        if not dry_run:
            from app.services.matching import _active_not_expired_query
            total_live = _active_not_expired_query(today).count()

    summary = {
        "date": today.isoformat(),
        "label": label,
        "dry_run": dry_run,
        "candidates": len(outcomes),
        "inserted": len(inserted_ids) if not dry_run else sum(o.accepted for o in outcomes),
        "duplicates": sum(1 for o in outcomes if o.duplicate),
        "rejected": sum(1 for o in outcomes if not o.accepted and not o.duplicate),
        "db_error": db_error,
        "live_scholarships_now": total_live,
        "inserted_ids": inserted_ids,
    }
    report_path = write_report(outcomes, summary)
    summary["report"] = str(report_path)
    return summary


def write_report(outcomes: list[Outcome], summary: dict) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    suffix = "-dry-run" if summary["dry_run"] else ""
    label = f"-{summary['label']}" if summary.get("label") else ""
    path = REPORTS_DIR / f"{summary['date']}{label}{suffix}.md"

    def money(v):
        return f"${v:,.0f}" if isinstance(v, (int, float)) else "?"

    lines = [
        f"# Scholarship discovery report: {summary['date']}" + (" (dry run, nothing inserted)" if summary["dry_run"] else ""),
        "",
        f"- Candidates researched: **{summary['candidates']}**",
        f"- {'Would add' if summary['dry_run'] else 'Added'}: **{summary['inserted']}**",
        f"- Already in database: {summary['duplicates']}",
        f"- Rejected (failed a safety check): {summary['rejected']}",
    ]
    if summary.get("live_scholarships_now") is not None:
        lines.append(f"- Scholarships students can see now: **{summary['live_scholarships_now']}**")
    if summary.get("db_error"):
        lines += ["", f"**Database error, nothing was inserted:** {summary['db_error']}"]

    added = [o for o in outcomes if o.accepted]
    lines += ["", "## Added" if not summary["dry_run"] else "## Would add", ""]
    if added:
        lines += ["| Scholarship | Amount | Deadline | Who | Link |", "|---|---|---|---|---|"]
        for o in added:
            c = o.candidate
            who = ", ".join(c.get("grade_levels") or []) + (f" · {', '.join(c['states'])}" if c.get("states") else " · national")
            lines.append(
                f"| {c['title']} ({c['organization']}) | {'Varies' if c.get('amount_varies') is True else money(c.get('amount'))} | "
                f"{c.get('deadline') or 'rolling'} | {who} | {c['source_url']} |"
            )
    else:
        lines.append("Nothing new passed every check today.")

    rejected = [o for o in outcomes if not o.accepted and not o.duplicate]
    if rejected:
        lines += ["", "## Rejected", ""]
        for o in rejected:
            c = o.candidate
            lines.append(f"- **{c.get('title', '?')}** ({c.get('source_url', 'no link')}): {'; '.join(o.reasons)}")

    dups = [o for o in outcomes if o.duplicate]
    if dups:
        lines += ["", "## Already in database", ""]
        lines += [f"- {o.candidate.get('title')}: {o.duplicate}" for o in dups]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def undo(day: str) -> int:
    """Soft-removes one day's batch: deactivated, not deleted, so any
    student who already saved one still sees it in their list."""
    from app import create_app
    from app.extensions import db
    from app.models import Scholarship

    datetime.strptime(day, "%Y-%m-%d")
    source = f"daily_discovery_{day.replace('-', '_')}"
    app = create_app("development")
    with app.app_context():
        rows = Scholarship.query.filter_by(source_name=source).all()
        for row in rows:
            row.is_active = False
            row.status = "unavailable"
        db.session.commit()
        return len(rows)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Validate and insert discovered scholarships.")
    parser.add_argument("inbox", nargs="?", help="path to the day's candidates JSON")
    parser.add_argument("--dry-run", action="store_true", help="check everything, insert nothing")
    parser.add_argument("--undo", metavar="YYYY-MM-DD", help="deactivate everything added on that day")
    parser.add_argument("--max", type=int, default=MAX_INSERTS_PER_RUN, help="insert cap for this run (backfills)")
    parser.add_argument("--label", help="report name suffix, e.g. state-grants")
    args = parser.parse_args(argv)

    if args.undo:
        print(json.dumps({"undone": undo(args.undo), "date": args.undo}))
        return 0
    if not args.inbox:
        parser.error("give a candidates file, or --undo DATE")

    if args.label and not re.fullmatch(r"[a-z0-9-]{1,40}", args.label):
        parser.error("--label must be lowercase letters, digits and dashes")
    summary = run(Path(args.inbox), dry_run=args.dry_run, max_inserts=args.max, label=args.label)
    # Last line is machine-readable for the scheduled task to report from.
    print(json.dumps(summary))
    return 2 if summary["db_error"] else 0


if __name__ == "__main__":
    sys.exit(main())
