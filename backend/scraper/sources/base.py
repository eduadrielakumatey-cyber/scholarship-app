"""
scraper/sources/base.py
--------------------------
Every place we pull scholarship data from (a partner API, a public listings
page, a CSV a counselor emails us, etc.) implements this interface. The
orchestrator (scraper/run_scraper.py) doesn't care HOW a source gets its
data, only that it returns a list of normalized dicts shaped like
NORMALIZED_FIELDS below.

To add a new source: create a new file in scraper/sources/, subclass
ScholarshipSource, implement fetch(), and register it in run_scraper.py's
SOURCES list.
"""

from abc import ABC, abstractmethod

# Every source's fetch() must return a list of dicts with (at least) these
# keys. Optional keys can be omitted and will fall back to model defaults.
NORMALIZED_FIELDS = {
    "external_id",       # required, unique within this source
    "title",              # required
    "organization",
    "description",
    "amount",              # required, float
    "deadline",            # ISO date string "YYYY-MM-DD" or None
    "min_gpa",
    "grade_levels",        # list[str]
    "states",              # list[str], [] = national
    "demographics",        # list[str]
    "majors",              # list[str]
    "interests",           # list[str]
    "estimated_hours_to_apply",
    "estimated_applicant_pool",
    "num_awards",
    "source_url",
}


class ScholarshipSource(ABC):
    """Base class every scraper source must implement."""

    #: Stored on each Scholarship row as `source_name`, used for de-duping.
    name: str = "unnamed_source"

    @abstractmethod
    def fetch(self) -> list[dict]:
        """
        Return a list of normalized scholarship dicts (see NORMALIZED_FIELDS).
        Should raise on hard failures (e.g. network error) so the
        orchestrator can log it and move on to the next source rather than
        silently returning an empty list and looking like "no new
        scholarships today."
        """
        raise NotImplementedError

    @staticmethod
    def estimate_hours_from_description(description: str) -> float:
        """
        Cheap heuristic when a source doesn't explicitly state estimated
        effort: look for signals like "essay" (more effort) vs. "no essay
        required" (less effort). Real scraped sources should override this
        with better signals where available (e.g. number of required
        documents).
        """
        if not description:
            return 2.0
        text = description.lower()
        if "no essay" in text or "auto" in text:
            return 0.5
        if "essay" in text and ("multiple essays" in text or "two essays" in text):
            return 5.0
        if "essay" in text:
            return 3.0
        return 1.5

    @staticmethod
    def estimate_applicant_pool(amount: float) -> int:
        """
        Cheap heuristic when a source doesn't report a real applicant
        count. Mirrors the bucket logic in app/services/scoring.py so a
        scraped scholarship behaves consistently with seeded ones.
        """
        if amount < 1000:
            return 800
        if amount < 5000:
            return 2500
        if amount < 20000:
            return 4000
        return 6000
