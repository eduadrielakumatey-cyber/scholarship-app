"""
backfill_award_structure.py
------------------------------
Fills in award_frequency / renewable / renewal_years for the small set of
scholarships whose real-world structure was independently verified via
web research in a prior session (see the award-data audit in this
project's history for citations). Everything else in the database stays
'unknown' -- this script deliberately does NOT guess based on keywords,
award size, or category. Only records with an explicit, sourced dollar
breakdown are touched.

Two of these also correct award_amount itself: NALC and APWU were
originally seeded with their 4-year TOTAL ($16,000 / $8,000) rather than
the per-disbursement amount, which is what award_amount is now defined to
mean. Correcting them here keeps maximum_total_award (award_amount *
renewal_years) from double-counting.

Cameron Impact, Coolidge, and Boettcher are deliberately NOT included
here even though they're known to be multi-year full-ride awards: their
stated dollar figure is an estimate of total value (tuition varies by
school), not a confirmed per-year amount, so encoding them as
'annual'/renewable with the current figure as award_amount would produce
an inflated maximum_total_award (e.g. $100,000 x 4). They stay 'unknown'
until a real per-year figure is sourced.

Safe to re-run (idempotent -- just re-applies the same values).

Run with:
    python backfill_award_structure.py
"""

from app import create_app
from app.extensions import db
from app.models import Scholarship

# id -> (award_amount, renewal_years). All are award_frequency='annual',
# renewable=True.
VERIFIED_ANNUAL_RENEWABLE = {
    313: (12500, 4),  # Mabel and Lawrence S. Cooke: "$50,000 (up to $12,500/year for four years)"
    319: (1500, 4),   # Elks National Foundation Legacy Award: "$6,000 (payable at $1,500/year over four years)"
    316: (25000, 4),  # Buick Achievers: "$25,000... renewable for up to four years"
    332: (4000, 4),   # NALC William C. Doherty: "$4,000 per year (renewable up to 4 years)" -- was stored as the $16,000 total
    333: (2000, 4),   # APWU C. Hallbeck Memorial: "$8,000 total ($2,000/year for 4 years)" -- was stored as the $8,000 total
}


def run():
    app = create_app("development")
    with app.app_context():
        updated = 0
        for scholarship_id, (per_year_amount, years) in VERIFIED_ANNUAL_RENEWABLE.items():
            scholarship = Scholarship.query.get(scholarship_id)
            if not scholarship:
                print(f"id {scholarship_id} not found -- skipping")
                continue
            scholarship.award_amount = per_year_amount
            scholarship.award_frequency = "annual"
            scholarship.renewable = True
            scholarship.renewal_years = years
            updated += 1
        db.session.commit()
        print(f"Updated {updated} verified annual/renewable records.")

        counts = db.session.execute(
            db.text("SELECT award_frequency, count(*) FROM scholarships GROUP BY award_frequency")
        ).all()
        print("award_frequency distribution now:", counts)


if __name__ == "__main__":
    run()
