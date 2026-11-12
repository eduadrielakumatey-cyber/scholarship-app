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
    # True when the official page says the amount varies (or lists $0.00):
    # award_amount is then 0 and students see "Amount varies".
    amount_varies = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
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
    # The one college a winner must attend (e.g. an award posted on
    # Salisbury University's own scholarship portal). NULL = any school.
    school = db.Column(db.String(160), nullable=True)

    # --- Effort / value inputs for the scoring engine ---
    # Estimated hours a typical applicant spends on essays/forms. Defaults to
    # a conservative 2 hours when the scraper can't infer it from the listing.
    estimated_hours_to_apply = db.Column(db.Float, nullable=False, default=2.0)

    # Whether the application asks for an essay or personal statement.
    # NULL = not checked / the official page didn't say, and the card shows
    # no essay tag rather than guessing. Filled by scraper/essay_backfill.py.
    essay_required = db.Column(db.Boolean, nullable=True)

    # Estimated number of applicants. This drives the "chance of winning"
    # heuristic. If the source lists a real applicant count, the scraper
    # stores that. Otherwise we fall back to a rough bucket by award size
    # (see scraper/sources/base.py: estimate_applicant_pool()).
    estimated_applicant_pool = db.Column(db.Integer, nullable=False, default=500)
    num_awards = db.Column(db.Integer, nullable=False, default=1)  # how many winners are picked

    # --- Source tracking, used by the scraper to avoid duplicate inserts ---
    source_name = db.Column(db.String(120), nullable=True)     # e.g. "Fastweb", "manual_seed"
    source_url = db.Column(db.String(500), nullable=True)
    # Separate application link, when the provider's official/info page
    # (source_url) isn't itself where you apply (e.g. a foundation's
    # overview page that links out to a portal). NULL means "same as
    # source_url" -- there is no second link to show.
    application_url = db.Column(db.String(500), nullable=True)
    external_id = db.Column(db.String(255), nullable=True, index=True)

    is_active = db.Column(db.Boolean, default=True)  # set False instead of deleting expired ones

    # --- Link-health tracking (see scraper/link_checker.py) ---
    # A diagnostic status distinct from is_active: is_active is the single
    # boolean matching.py actually filters on (unchanged by this column),
    # while `status` records WHY, so a human/future job can tell "verified
    # working" apart from "never checked" apart from "confirmed dead."
    #   active        -- last check succeeded and looked like a real listing
    #   expired       -- deadline passed but the program looks recurring;
    #                    still shown (matching.py already excludes anything
    #                    with a passed deadline on its own) until its next
    #                    cycle's date is found
    #   unavailable   -- confirmed dead (404/410/DNS failure/explicit
    #                    "program discontinued" language) -- also sets
    #                    is_active=False
    #   needs_review  -- link check was inconclusive (timeout, redirect
    #                    loop, non-2xx that isn't clearly "gone") and a
    #                    human should look rather than the job guessing
    #   upcoming      -- reserved for a future cycle that hasn't opened yet
    # Defaults to needs_review, not active: a row that has never been
    # checked has not earned "active" -- that has to be verified, not
    # assumed. See migration d9a3f61c8e2b for the one-time backfill logic
    # applied to rows that existed before this column did.
    status = db.Column(db.String(20), nullable=False, default="needs_review")
    last_verified_at = db.Column(db.DateTime, nullable=True)

    # Whether the OPPORTUNITY ITSELF (not the award payout -- see
    # award_frequency/renewable above, which describe a single winner's
    # payout schedule) runs again next year. NULL = unknown/not yet
    # determined. Used by the freshness job to decide which expired-dated
    # rows are worth re-checking for a reopened next cycle vs. leaving
    # alone as a one-time award that has simply run its course.
    is_recurring_program = db.Column(db.Boolean, nullable=True)

    # --- Posted on ScholarMatch by a sponsor (applied to inside the app) ---
    # hosted rows have no outside source_url; students apply in the app and
    # the sponsor reviews applications through a private link. Sponsor
    # contact details and the review-link hash are never sent to students.
    hosted = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    essay_prompt = db.Column(db.Text, nullable=True)
    sponsor_name = db.Column(db.String(160), nullable=True)
    sponsor_email = db.Column(db.String(255), nullable=True)
    review_token_hash = db.Column(db.String(64), nullable=True, unique=True)

    # The official application's questions, word for word, so students can
    # answer them in the app (see app/services/questions.py). [] = none.
    questions = db.Column(db.JSON, nullable=True)

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
            "amount_varies": self.amount_varies,
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
            "school": self.school,
            "estimated_hours_to_apply": self.estimated_hours_to_apply,
            "essay_required": self.essay_required,
            "num_awards": self.num_awards,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "application_url": self.application_url or self.source_url,
            "status": self.status,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "is_recurring_program": self.is_recurring_program,
            "hosted": bool(self.hosted),
            "essay_prompt": self.essay_prompt,
            "questions": self.questions or [],
        }
