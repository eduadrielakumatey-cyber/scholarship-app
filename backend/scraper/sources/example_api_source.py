"""
scraper/sources/example_api_source.py
----------------------------------------
TEMPLATE: this is a worked example showing how to plug in a real
scholarship-data provider that exposes a JSON API. There is no single
universal "scholarships API" -- you need to sign up with an actual
provider (examples to evaluate: Bold.org's partner API, Scholarships.com's
data licensing program, going.gov / Federal Student Aid open data, or a
state higher-education-commission open-data portal) and get real
credentials and a real endpoint, then fill in BASE_URL / API_KEY handling
below.

This file is written so it WILL run (it won't crash), but `fetch()`
returns an empty list until SCHOLARSHIP_API_BASE_URL is configured, so the
scraper doesn't accidentally hit a placeholder URL and insert garbage data.
"""

import os

import requests

from scraper.sources.base import ScholarshipSource


class ExampleApiSource(ScholarshipSource):
    name = "example_partner_api"

    BASE_URL = os.environ.get("SCHOLARSHIP_API_BASE_URL", "")
    API_KEY = os.environ.get("SCHOLARSHIP_API_KEY", "")

    def fetch(self) -> list[dict]:
        if not self.BASE_URL:
            # Not configured yet -- skip quietly rather than erroring, so
            # the scraper still runs cleanly for users who haven't signed
            # up with a provider yet.
            return []

        response = requests.get(
            f"{self.BASE_URL}/v1/scholarships",
            headers={"Authorization": f"Bearer {self.API_KEY}"},
            params={"per_page": 100, "active": "true"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()

        normalized = []
        for item in payload.get("results", []):
            normalized.append(
                {
                    "external_id": str(item["id"]),
                    "title": item.get("name", "Untitled scholarship"),
                    "organization": item.get("sponsor"),
                    "description": item.get("description", ""),
                    "amount": float(item.get("award_amount", 0) or 0),
                    "deadline": item.get("deadline"),  # expect "YYYY-MM-DD"
                    "min_gpa": item.get("min_gpa"),
                    "grade_levels": item.get("eligible_grades", []),
                    "states": item.get("eligible_states", []),
                    "demographics": item.get("eligible_demographics", []),
                    "majors": item.get("eligible_majors", []),
                    "interests": item.get("tags", []),
                    "estimated_hours_to_apply": self.estimate_hours_from_description(
                        item.get("description", "")
                    ),
                    "estimated_applicant_pool": self.estimate_applicant_pool(
                        float(item.get("award_amount", 0) or 0)
                    ),
                    "num_awards": item.get("num_awards", 1),
                    "source_url": item.get("url"),
                }
            )
        return normalized
