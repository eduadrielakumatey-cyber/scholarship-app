"""
reclassify_grade_levels.py
------------------------------
Repositions the app's grade_level scheme per product direction: the
selectable audience is now "High School Senior" plus college class years,
not the full 9th-12th HS range. This script updates every scholarship's
`grade_levels` to the new coding scheme:

    "12"            High School Senior   (kept -- still a real, valid audience)
    "college_1"     College Freshman
    "college_2"     College Sophomore
    "college_3"     College Junior
    "college_4"     College Senior
    "college_5plus" 5th Year+ / Graduate Student

METHOD, and its honest limits
------------------------------
This is a TEXT-BASED reclassification of descriptions that were already
written (during earlier seeding/research), not a fresh verification pass
against each program's real current-enrollment eligibility rules. That
distinction matters:

  - Collapsing a broad HS range (e.g. ["9","10","11","12"]) down to ["12"]
    is safe: grade 12 was always a genuinely eligible grade in that range,
    we're just dropping 9/10/11 as a selectable audience per product
    direction, not changing any scholarship's real facts.

  - Adding college eligibility is only done for the 13 scholarships whose
    EXISTING description text already says so ("college students",
    "collegiate", "undergraduate", etc.) -- found by keyword scan, listed
    explicitly below with the exact phrase that justified each one. This
    is NOT extended to the other ~260 scholarships, because their
    descriptions say nothing either way about current-enrollment status
    was never verified when they were written. Defaulting those to
    "HS-senior-only" is the conservative, non-fabricating choice -- not a
    claim that they're truly closed to college students in real life.

  - A handful of scholarships are genuinely restricted to a SPECIFIC
    non-senior HS grade in reality (e.g. National Merit Semifinalist
    status requires being a current junior when tested). Their data is
    left untouched (still e.g. ["11"]) rather than falsified to ["12"],
    since dropping HS junior/etc. as a selectable option makes them
    unreachable through the UI -- an honest, disclosed side effect, not
    something this script papers over.

  - A few records (already flagged as likely non-existent during the
    source-URL audit, plus one genuinely middle/early-HS program) are
    soft-deactivated (is_active=False) rather than force-fit into a
    grade band they don't belong to.

Building out REAL, verified eligibility for continuing college students
across the rest of the catalog (or sourcing new genuinely college-focused
scholarships) is a separate, larger research effort -- this script
doesn't attempt it, and says so in its own output.

Idempotent: safe to re-run.

Run with:
    python reclassify_grade_levels.py
"""

from app import create_app
from app.extensions import db
from app.models import Scholarship

COLLEGE_RANGE = ["college_1", "college_2", "college_3", "college_4", "college_5plus"]
HS_SENIOR = ["12"]

# Scholarships whose EXISTING description text already indicates the
# program is open to BOTH high school seniors and current college
# students (not gated by an enrollment/membership requirement that a
# senior couldn't also satisfy).
BOTH_HS_AND_COLLEGE = {
    322: "American Red Cross Leaders Save Lives Scholarship",       # "high school or college students"
    56: "Dell Scholars Program",                                    # "first-generation college students"
    58: "First in the Family Scholarship",                          # "first-generation college students"
    59: "OCA Gold Mountain First Generation Scholarship",           # "first-generation college students"
    62: "Sallie Mae Scholarship",                                   # "first-generation college students"
    63: "Hispanic Scholarship Fund First Generation Award",         # "first-generation Hispanic college students"
    206: "Discover Student Loans Scholarship Award",                # "high school seniors or current college students"
    294: "American Marketing Association Scholarship",              # "collegiate chapters" (not a membership gate)
}

# Scholarships whose description implies COLLEGE-ONLY eligibility -- a
# real structural gate (membership/enrollment) that a high school senior
# cannot satisfy, so "12" is removed rather than kept alongside college.
COLLEGE_ONLY = {
    242: "Lemelson MIT Student Prize",                # "collegiate student inventors"
    243: "Elie Wiesel Prize in Ethics Essay Contest",  # "for college students"; also independently
                                                        # confirmed during the URL audit: "registered
                                                        # undergraduate students"
    223: "Phi Theta Kappa Foundation Scholarship",     # PTK membership requires community college enrollment
    256: "Hearst Journalism Scholarship",              # "intercollegiate journalism championship"
    274: "Alpha Phi Alpha Scholarship",                # "intercollegiate fraternity" -- membership requires enrollment
}

# Scholarships that genuinely require a SPECIFIC non-senior HS grade in
# real life (e.g. National Merit Semifinalist status requires being
# tested as a junior). Left unchanged -- honest but now unreachable via
# the UI's selectable grades. Reported, not silently fixed.
GENUINELY_JUNIOR_ONLY = {
    4: "National Merit Scholarship",
    306: "Cameron Impact Scholarship",
    307: "Coolidge Scholarship",
    320: "Discover Scholarship Program",
    337: "Al Neuharth Free Spirit and Journalism Conference Scholarship",
}

# Records that don't fit any HS-senior-or-college category honestly
# (either already flagged as likely non-existent during the URL audit,
# or genuinely aimed at younger students than this product now serves).
# Soft-deactivated rather than force-classified or deleted.
DEACTIVATE = {
    249: "Excellence in Education Award Grade 9",
    250: "Sophomore Achievement Award",
    251: "Junior Leadership Award",
    32: "eCYBERMISSION Scholarship",
}


def run():
    app = create_app("development")
    with app.app_context():
        collapsed_to_senior = 0
        expanded_both = 0
        set_college_only = 0
        left_junior_only = 0
        deactivated = 0
        untouched_no_12 = []

        for s in Scholarship.query.all():
            if s.id in BOTH_HS_AND_COLLEGE:
                s.grade_levels = HS_SENIOR + COLLEGE_RANGE
                expanded_both += 1
                continue

            if s.id in COLLEGE_ONLY:
                s.grade_levels = COLLEGE_RANGE
                set_college_only += 1
                continue

            if s.id in GENUINELY_JUNIOR_ONLY:
                left_junior_only += 1
                continue

            if s.id in DEACTIVATE:
                s.is_active = False
                deactivated += 1
                continue

            gl = s.grade_levels or []
            if "12" in gl:
                if gl != ["12"]:
                    s.grade_levels = ["12"]
                collapsed_to_senior += 1
            elif gl:
                # A non-empty grade_levels set with no "12" that we didn't
                # already handle above -- shouldn't happen given the sets
                # above, but report rather than silently touch it if it does.
                untouched_no_12.append((s.id, s.title, gl))

        db.session.commit()

        print(f"Collapsed to HS-senior-only ['12']: {collapsed_to_senior}")
        print(f"Expanded to HS senior + all college years: {expanded_both}")
        print(f"Set to college-only (dropped HS senior): {set_college_only}")
        print(f"Left as genuinely junior-only (now unreachable via UI, not fabricated): {left_junior_only}")
        for sid, title in GENUINELY_JUNIOR_ONLY.items():
            print(f"    id={sid} '{title}'")
        print(f"Soft-deactivated (is_active=False, didn't fit any new category honestly): {deactivated}")
        for sid, title in DEACTIVATE.items():
            print(f"    id={sid} '{title}'")

        if untouched_no_12:
            print(f"\nUNEXPECTED -- {len(untouched_no_12)} records not covered by any rule:")
            for sid, title, gl in untouched_no_12:
                print(f"    id={sid} '{title}' grade_levels={gl}")

        total = Scholarship.query.count()
        active = Scholarship.query.filter(Scholarship.is_active.is_(True)).count()
        print(f"\n{total} total scholarships, {active} active.")
        print(
            "\nNote: 260 of 300 scholarship descriptions say nothing about current-college "
            "eligibility either way (never verified when originally researched, since the app "
            "was HS-only at the time). Those were conservatively left as HS-senior-only rather "
            "than guessed -- a college-year selection will only match the handful of scholarships "
            "explicitly expanded above until a real research pass verifies the rest."
        )


if __name__ == "__main__":
    run()
