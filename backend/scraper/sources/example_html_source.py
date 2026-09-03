"""
scraper/sources/example_html_source.py
-----------------------------------------
TEMPLATE: shows the shape of an HTML-scraping source for a public listings
page that does not offer an API. Disabled by default (`ENABLED = False`)
because:

  1. It points at a placeholder URL, not a real site.
  2. Before scraping any real website, you must check that site's
     robots.txt and Terms of Service for whether automated scraping is
     permitted, and add rate limiting / a descriptive User-Agent. Many
     scholarship-listing sites either disallow scraping or offer a
     paid/partner data feed instead -- prefer that feed (see
     example_api_source.py) whenever one exists.

To use this for a real, scraping-permitted site: set ENABLED = True,
point BASE_URL at the real listings page, and adjust the CSS selectors in
_parse_listing() to match that page's actual HTML structure (inspect it in
your browser's dev tools first).
"""

import requests
from bs4 import BeautifulSoup

from scraper.sources.base import ScholarshipSource


class ExampleHtmlSource(ScholarshipSource):
    name = "example_html_listing"
    ENABLED = False
    BASE_URL = "https://example-scholarship-listings.invalid/browse"

    HEADERS = {
        "User-Agent": "ScholarshipMatchBot/1.0 (+contact: youremail@example.com)"
    }

    def fetch(self) -> list[dict]:
        if not self.ENABLED:
            return []

        response = requests.get(self.BASE_URL, headers=self.HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        normalized = []
        # Placeholder selector -- replace ".scholarship-card" with whatever
        # the real page actually uses once ENABLED is turned on.
        for card in soup.select(".scholarship-card"):
            parsed = self._parse_listing(card)
            if parsed:
                normalized.append(parsed)
        return normalized

    def _parse_listing(self, card) -> dict | None:
        title_el = card.select_one(".scholarship-title")
        amount_el = card.select_one(".scholarship-amount")
        link_el = card.select_one("a")

        if not title_el or not link_el:
            return None

        title = title_el.get_text(strip=True)
        amount_text = amount_el.get_text(strip=True) if amount_el else "0"
        amount = float("".join(ch for ch in amount_text if ch.isdigit()) or 0)
        url = link_el.get("href", "")
        description = card.get_text(" ", strip=True)

        return {
            "external_id": url,  # using the URL as a stable unique id
            "title": title,
            "organization": None,
            "description": description,
            "amount": amount,
            "deadline": None,
            "min_gpa": None,
            "grade_levels": [],
            "states": [],
            "demographics": [],
            "majors": [],
            "interests": [],
            "estimated_hours_to_apply": self.estimate_hours_from_description(description),
            "estimated_applicant_pool": self.estimate_applicant_pool(amount),
            "num_awards": 1,
            "source_url": url,
        }
