"""
app/models/scholarship.py
--------------------------
Represents a single scholarship opportunity, populated either by the seed
script (seed_data.py) or by the nightly scraper (scraper/run_scraper.py).

Three groups of fields matter most:

1. Eligibility fields (min_gpa, grade_levels, states, demographics,
   majors, interests, majors_are_hard_requirement) -> used to decide
   whether a user is even allowed to apply, and how *closely* they match
   if eligible.

2. Award-structure fields (award_amount, award_frequency, renewable,
   renewal_years) -> describe what a single disbursement is worth and
   whether it recurs. See maximum_total_award below for why the "total"
   figure is computed rather than stored.

3. Effort/value fields (estimated_hours_to_apply, estimated_applicant_pool,
   num_awards) -> used by app/services/scoring.py to compute the
   competitiveness estimate, dollars-per-hour, and expected value.

`source_name` + `source_url` + `external_id` let the scraper de-duplicate:
the same scholarship should not be inserted twice if it's seen on two
different scrape runs.
"""

from datetime import datetime

from sqlalchemy.dialects.postgresql import ARRAY

from app.extensions import db


class Scholarship(db.Model):
    __tablename__ = "scholarships"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.Date, nullable=True)

    # --- Award structure. See maximum_total_award for how these combine. ---
    # The value of a SINGLE disbursement -- not necessarily the total a
    # winner could receive if the award is annual and renewable.
    award_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    # 'one_time' | 'annual' | 'unknown'. Defaults to 'unknown', not
    # 'one_time' -- a lack of evidence about recurrence is not the same as
    # verified evidence there isn't any. See backfill_award_structure.py
    # for the (small, cited) set of records where this has been confirmed.
    award_frequency = db.Column(db.String(10), nullable=False, default="unknown")
    # Only meaningful when award_frequency == 'annual'. NULL means unknown,
    # not "no" -- do not read a NULL/False value here as a confirmed fact.
    renewable = db.Column(db.Boolean, nullable=True)
    renewal_years = db.Column(db.Integer, nullable=True)  # e.g. 4

    # --- Eligibility criteria. Empty list/None on any of these means
    # "no restriction" (open to everyone on that dimension). ---
    min_gpa = db.Column(db.Float, nullable=True)
    grade_levels = db.Column(ARRAY(db.String), default=list)   # e.g. ["12"] or ["college_1", ..., "college_5plus"]
    states = db.Column(ARRAY(db.String), default=list)          # e.g. ["MD", "VA"], [] = national
    demographics = db.Column(ARRAY(db.String), default=list)    # e.g. ["first-generation"]
    majors = db.Column(ARRAY(db.String), default=list)          # e.g. ["engineering"]
    interests = db.Column(ARRAY(db.String), default=list)       # e.g. ["robotics", "stem"]
    # If True, a major listed above is a hard eligibility requirement (e.g.
    # a fund legally restricted to nursing students). If False (default), a
    # listed major is only a Match Quality signal -- a related-but-not-exact
    # major is still shown, just ranked lower, instead of being hidden.
    majors_are_hard_requirement = db.Column(db.Boolean, nullable=False, default=False)

    # --- Effort / value inputs for the scoring engine ---
    # Estimated hours a typical applicant spends on essays/forms. Defaults to
    # a conservative 2 hours when the scraper can't infer it from the listing.
    estimated_hours_to_apply = db.Column(db.Float, nullable=False, default=2.0)

    # Estimated number of applicants. This drives the "chance of winning"
    # heuristic. If the source lists a real applicant count, the scraper
    # stores that. Otherwise we fall back to a rough bucket by award size
    # (see scraper/sources/base.py: estimate_applicant_pool()).
    estimated_applicant_pool = db.Column(db.Integer, nullable=False, default=500)
    num_awards = db.Column(db.Integer, nullable=False, default=1)  # how many winners are picked

    # --- Source tracking, used by the scraper to avoid duplicate inserts ---
    source_name = db.Column(db.String(120), nullable=True)     # e.g. "Fastweb", "manual_seed"
    source_url = db.Column(db.String(500), nullable=True)
    external_id = db.Column(db.String(255), nullable=True, index=True)

    is_active = db.Column(db.Boolean, default=True)  # set False instead of deleting expired ones
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("source_name", "external_id", name="uq_source_external_id"),
    )

    @property
    def maximum_total_award(self) -> float:
        """
        The largest total dollar value this award could represent across
        its full renewal period, computed rather than stored -- storing it
        as its own column would let it silently drift out of sync with
        award_amount/renewal_years if either changed. Only multiplies out
        when frequency and renewability have actually been verified
        (award_frequency == 'annual' and renewable is True); otherwise this
        is just award_amount itself, treated as a floor on the true value
        rather than a claim about it.
        """
        base = float(self.award_amount) if self.award_amount is not None else 0.0
        if self.award_frequency == "annual" and self.renewable and self.renewal_years:
            return base * self.renewal_years
        return base

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "organization": self.organization,
            "description": self.description,
            # "amount" kept for backward compatibility with existing
            # frontend code; "award_amount" is the same value under its
            # proper name going forward.
            "amount": float(self.award_amount) if self.award_amount is not None else 0.0,
            "award_amount": float(self.award_amount) if self.award_amount is not None else 0.0,
            "award_frequency": self.award_frequency,
            "renewable": self.renewable,
            "renewal_years": self.renewal_years,
            "maximum_total_award": self.maximum_total_award,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "min_gpa": self.min_gpa,
            "grade_levels": self.grade_levels or [],
            "states": self.states or [],
            "demographics": self.demographics or [],
            "majors": self.majors or [],
            "interests": self.interests or [],
            "majors_are_hard_requirement": self.majors_are_hard_requirement,
            "estimated_hours_to_apply": self.estimated_hours_to_apply,
            "num_awards": self.num_awards,
            "source_name": self.source_name,
            "source_url": self.source_url,
        }
