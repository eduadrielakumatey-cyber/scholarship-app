"""
seed_data.py
--------------
Populates the database with a handful of realistic sample scholarships so
the app is usable immediately after setup, without waiting on the scraper.

Run with:
    python seed_data.py

Safe to re-run: it upserts on (source_name, external_id), so running it
twice won't create duplicates.
"""

from datetime import date

from app import create_app
from app.extensions import db
from app.models import Scholarship

SAMPLE_SCHOLARSHIPS = [
    dict(
        external_id="seed-001",
        title="Future Engineers National STEM Award",
        organization="National STEM Foundation",
        description="For students pursuing engineering or computer science majors with a record of STEM extracurriculars.",
        award_amount=2500,
        deadline=date(2026, 9, 15),
        min_gpa=3.2,
        grade_levels=["11", "12"],
        states=[],
        demographics=[],
        majors=["engineering", "computer science"],
        interests=["stem", "robotics", "coding"],
        estimated_hours_to_apply=3,
        estimated_applicant_pool=4000,
        num_awards=10,
    ),
    dict(
        external_id="seed-002",
        title="Maryland First-Generation Scholars Grant",
        organization="Maryland Higher Education Commission",
        description="Supports first-generation college students who are Maryland residents.",
        award_amount=4000,
        deadline=date(2026, 8, 1),
        min_gpa=2.8,
        grade_levels=["12"],
        states=["MD"],
        demographics=["first-generation"],
        majors=[],
        interests=[],
        estimated_hours_to_apply=2,
        estimated_applicant_pool=600,
        num_awards=15,
    ),
    dict(
        external_id="seed-003",
        title="Young Artists Creative Futures Award",
        organization="Arts Forward Alliance",
        description="For students with a strong portfolio in visual arts, music, or creative writing.",
        award_amount=1000,
        deadline=date(2026, 7, 20),
        min_gpa=None,
        grade_levels=["9", "10", "11", "12"],
        states=[],
        demographics=[],
        majors=["art", "music", "fine arts"],
        interests=["art", "music", "writing"],
        estimated_hours_to_apply=4,
        estimated_applicant_pool=1500,
        num_awards=5,
    ),
    dict(
        external_id="seed-004",
        title="Community Service Leadership Scholarship",
        organization="Civic Impact Fund",
        description="Recognizes students with 100+ hours of documented volunteer service.",
        award_amount=500,
        deadline=date(2026, 10, 1),
        min_gpa=2.5,
        grade_levels=["10", "11", "12"],
        states=[],
        demographics=[],
        majors=[],
        interests=["community service", "leadership"],
        estimated_hours_to_apply=1.5,
        estimated_applicant_pool=2500,
        num_awards=25,
    ),
    dict(
        external_id="seed-005",
        title="Women in Technology Rising Star Award",
        organization="WomenTech Forward",
        description="For young women pursuing degrees in technology or computer science.",
        award_amount=10000,
        deadline=date(2026, 11, 30),
        min_gpa=3.5,
        grade_levels=["12"],
        states=[],
        demographics=["female"],
        majors=["computer science", "information technology"],
        interests=["stem", "coding"],
        estimated_hours_to_apply=6,
        estimated_applicant_pool=3000,
        num_awards=3,
    ),
    dict(
        external_id="seed-006",
        title="Small Town Roots Scholarship",
        organization="Rural Futures Trust",
        description="For students graduating from a high school in a town under 20,000 people.",
        award_amount=750,
        deadline=date(2026, 8, 15),
        min_gpa=2.0,
        grade_levels=["12"],
        states=[],
        demographics=["rural"],
        majors=[],
        interests=[],
        estimated_hours_to_apply=1,
        estimated_applicant_pool=900,
        num_awards=20,
    ),
]


def run_seed():
    app = create_app("development")
    with app.app_context():
        for entry in SAMPLE_SCHOLARSHIPS:
            existing = Scholarship.query.filter_by(
                source_name="manual_seed", external_id=entry["external_id"]
            ).first()
            if existing:
                for key, value in entry.items():
                    setattr(existing, key, value)
            else:
                db.session.add(Scholarship(source_name="manual_seed", **entry))
        db.session.commit()
        print(f"Seeded {len(SAMPLE_SCHOLARSHIPS)} scholarships.")


if __name__ == "__main__":
    run_seed()
