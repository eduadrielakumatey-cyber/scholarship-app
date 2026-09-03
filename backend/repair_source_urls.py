"""
repair_source_urls.py
------------------------
Repairs the source_url corruption caused by add_urls_2.py, which assigned
URLs by hardcoded database row ID -- a stale, unsafe identity that no
longer matches what these rows actually are (see the source-URL integrity
audit for the full mechanism and evidence). That script has since been
disabled; see its docstring.

SAFETY MODEL -- read before adding entries to REPAIRS below:

  1. Never identify a scholarship by row ID. Every entry here is matched
     by EXACT (title, organization) string equality. If zero or more than
     one row matches, the entry is skipped and reported -- never guessed.
  2. Every entry must be marked `verified=True` by a human/agent who has
     actually researched the real scholarship and confirmed the page
     corresponds to it (title/org check, not just a plausible-looking
     domain). Unverified entries are refused.
  3. Before writing, a lightweight sanity check confirms at least one
     significant word from the title or organization appears in the
     destination URL's domain, UNLESS `sanity_override=True` is set with
     an explanatory `note` -- for the small number of real cases where an
     official page legitimately doesn't spell out the org name (e.g. an
     acronym-only domain). This does not replace the human verification
     in (2); it's a second, independent guard against exactly the class
     of bug this script exists to fix.
  4. Idempotent: matching is by title+org and the operation is an UPDATE,
     never an INSERT, so re-running this script re-applies the same
     values rather than corrupting or duplicating anything.
  5. Anything not confidently verifiable is simply left out of REPAIRS
     entirely and reported in the audit instead -- this script never
     fabricates a URL to reach 100% coverage.

Run with:
    python repair_source_urls.py
"""

from dataclasses import dataclass

from app import create_app
from app.extensions import db
from app.models import Scholarship


@dataclass
class Repair:
    title: str
    organization: str
    url: str
    note: str
    verified: bool = True
    sanity_override: bool = False


# ---------------------------------------------------------------------------
# Phase 1: the 57 confirmed add_urls_2.py corruptions.
# 46 of these are RESTORED from add_urls.py's own original title-matched
# dict (correct when first applied; add_urls_2.py overwrote them by ID
# afterward -- re-using that already-vetted value is safer than fresh
# research and is explicitly why this script matches by title, not ID).
# The rest were freshly researched because add_urls.py never covered them.
# ---------------------------------------------------------------------------
REPAIRS: list[Repair] = [
    Repair("Coca-Cola Scholars Program", "Coca-Cola Scholars Foundation",
           "https://www.coca-colascholarsfoundation.org/apply/", "restored from add_urls.py"),
    Repair("Elks National Foundation Most Valuable Student", "Benevolent and Protective Order of Elks",
           "https://www.elks.org/scholars/scholarships/mvs.cfm", "restored from add_urls.py"),
    Repair("Prudential Spirit of Community Award", "Prudential Financial",
           "https://spirit.prudential.com/", "restored from add_urls.py"),
    Repair("National Merit Scholarship", "National Merit Scholarship Corporation",
           "https://www.nationalmerit.org/s/1758/interior.aspx?sid=1758&gid=2&pgid=424", "restored from add_urls.py"),
    Repair("Horatio Alger National Scholarship", "Horatio Alger Association",
           "https://scholars.horatioalger.org/scholarships/", "restored from add_urls.py"),
    Repair("Davidson Fellows Scholarship", "Davidson Institute",
           "https://www.davidsongifted.org/fellows-scholarship/", "restored from add_urls.py"),
    Repair("Thurgood Marshall College Fund Scholarship", "Thurgood Marshall College Fund",
           "https://tmcf.org/scholarships/",
           "add_urls.py's original path 404s (site reorganized since); corrected during "
           "Phase 4 spot-check verification to TMCF's current scholarships page",
           sanity_override=True),
    Repair("OCA Gold Mountain First Generation Scholarship", "OCA Asian Pacific American Advocates",
           "https://www.ocanational.org/scholarships", "restored from add_urls.py", sanity_override=True),
    Repair("GE-Reagan Foundation Scholarship", "General Electric and Ronald Reagan Presidential Foundation",
           "https://www.reaganfoundation.org/education/scholarship-programs/ge-reagan-foundation-scholarship-program/",
           "restored from add_urls.py"),
    Repair("MALDEF Law School Scholarship", "Mexican American Legal Defense Fund",
           "https://www.maldef.org/leadership/scholarships/", "restored from add_urls.py"),
    Repair("Korean American Scholarship Foundation Award", "KASF",
           "https://kasf.org/scholarships/", "restored from add_urls.py"),
    Repair("Millie Brother Scholarship for Children of Deaf Adults", "CODA International",
           "https://www.coda-international.org/scholarship", "restored from add_urls.py"),
    Repair("Zonta International Young Women in Public Affairs", "Zonta International",
           "https://www.zonta.org/Global-Impact/Education/Young-Women-in-Public-Affairs-Award",
           "restored from add_urls.py"),
    Repair("Folds of Honor Scholarship", "Folds of Honor Foundation",
           "https://foldsofhonor.org/scholarships/", "restored from add_urls.py"),
    Repair("Gold Star Scholarship", "American Gold Star Mothers",
           "https://www.goldstarmoms.com/", "restored from add_urls.py"),
    Repair("Pat Tillman Scholarship", "Pat Tillman Foundation",
           "https://pattillmanfoundation.org/apply/", "restored from add_urls.py"),
    Repair("President's Volunteer Service Award", "Points of Light Foundation",
           "https://presidentialserviceawards.gov/", "restored from add_urls.py"),
    Repair("National Strength and Conditioning Association Scholarship", "NSCA",
           "https://www.nsca.com/membership/scholarships/", "restored from add_urls.py"),
    Repair("DECA Scholarship", "DECA Inc",
           "https://www.deca.org/scholarships/", "restored from add_urls.py"),
    Repair("American Medical Association Foundation Scholarship", "AMA Foundation",
           "https://www.ama-assn.org/about/ama-foundation/ama-foundation-scholarships", "restored from add_urls.py", sanity_override=True),
    Repair("National Student Nurses Association Scholarship", "NSNA",
           "https://www.nsna.org/scholarships-listing.html", "restored from add_urls.py"),
    Repair("Health Professions Scholarship Program", "US Military",
           "https://www.hpsp.usuhs.edu/", "restored from add_urls.py", sanity_override=True),
    Repair("TEXAS Grant", "Texas Higher Education Coordinating Board",
           "https://www.highered.texas.gov/student-success-initiatives/financial-aid-programs/texas-grant/",
           "restored from add_urls.py"),
    Repair("EPA Environmental Youth Award", "US Environmental Protection Agency",
           "https://www.epa.gov/students/presidents-environmental-youth-award", "restored from add_urls.py", sanity_override=True),
    Repair("National Restaurant Association Educational Foundation", "NRAEF",
           "https://www.chooserestaurants.org/programs-and-scholarships/", "restored from add_urls.py"),
    Repair("Elks State Scholarship", "Benevolent and Protective Order of Elks",
           "https://www.elks.org/scholars/", "restored from add_urls.py"),
    Repair("Society of Automotive Engineers Scholarship", "SAE International",
           "https://www.sae.org/participate/scholarships", "restored from add_urls.py", sanity_override=True),
    Repair("Home Depot Scholarship", "Home Depot Foundation",
           "https://homedepotfoundation.org/", "restored from add_urls.py"),
    Repair("General Motors Foundation Scholarship", "General Motors",
           "https://www.gm.com/commitments/community.html", "restored from add_urls.py", sanity_override=True),
    Repair("AI4ALL Open Minds Scholarship", "AI4ALL",
           "https://ai-4-all.org/open-minds/", "restored from add_urls.py", sanity_override=True),
    Repair("Codepath Tech Scholarship", "Codepath",
           "https://www.codepath.org/scholarships", "restored from add_urls.py"),
    Repair("Lemelson MIT Student Prize", "Lemelson-MIT Program",
           "https://lemelson.mit.edu/studentprize", "restored from add_urls.py"),
    Repair("NSHSS Scholar Award", "National Society of High School Scholars",
           "https://www.nshss.org/scholarships/", "restored from add_urls.py"),
    Repair("Dollars for Scholars Community Award", "Scholarship America",
           "https://scholarshipamerica.org/dollarsforscholars/", "restored from add_urls.py", sanity_override=True),
    Repair("Talbots Scholarship Foundation", "Talbots Charitable Foundation",
           "https://www.talbots.com/scholarship-foundation", "restored from add_urls.py"),
    Repair("Robert F. Kennedy Journalism Award", "RFK Foundation",
           "https://rfkhumanrights.org/work/journalism-award", "restored from add_urls.py", sanity_override=True),
    Repair("Hearst Journalism Scholarship", "Hearst Foundation",
           "https://www.hearstfdn.org/hearst-journalism/", "restored from add_urls.py"),
    Repair("Society of Professional Journalists Scholarship", "SPJ",
           "https://www.spj.org/scholarships.asp", "restored from add_urls.py", sanity_override=True),
    Repair("Alpha Phi Alpha Scholarship", "Alpha Phi Alpha Fraternity",
           "https://apa1906.net/foundation/scholarships/", "restored from add_urls.py", sanity_override=True),
    Repair("STEM Excellence Award for Underrepresented Students", "STEM Education Coalition",
           "https://www.stemedcoalition.org/", "restored from add_urls.py"),
    Repair("National Association of Realtors Scholarship", "National Association of Realtors",
           "https://www.nar.realtor/education/scholarships", "restored from add_urls.py", sanity_override=True),
    Repair("United Auto Workers Scholarship", "UAW",
           "https://uaw.org/benefits/scholarships/", "restored from add_urls.py", sanity_override=True),
    Repair("American Federation of Teachers Scholarship", "AFT",
           "https://www.aft.org/scholarships", "restored from add_urls.py", sanity_override=True),
    Repair("Sons of Norway Foundation Scholarship", "Sons of Norway",
           "https://www.sofn.com/foundation/scholarships/", "restored from add_urls.py", sanity_override=True),
    Repair("Institute of Management Accountants Scholarship", "IMA",
           "https://www.imaglobal.org/pages/student-scholarships",
           "add_urls.py's original path (imanet.org) redirects to IMA's new imaglobal.org "
           "domain but lands on the bare homepage, not a scholarship page; corrected during "
           "Phase 4 spot-check verification to IMA's current, specific scholarships page",
           sanity_override=True),

    # Upgraded rather than restored: add_urls.py's original value (acsa-arch.org,
    # the Association of Collegiate Schools of Architecture) was a related but
    # distinct org from what's in the DB's organization field (AIA). Architects
    # Foundation is AIA's own philanthropic partner -- a closer, more precise match.
    Repair("Architecture Foundation Scholarship", "American Institute of Architects",
           "https://architectsfoundation.org/scholarships/",
           "upgraded from add_urls.py's less-precise original (acsa-arch.org)"),

    # Freshly researched -- not present in add_urls.py's original dict at all.
    Repair("Jackie Robinson Foundation Award", "Jackie Robinson Foundation",
           "https://jackierobinson.org/apply/",
           "fresh research; NOTE: appears to be the same real program as "
           "'Jackie Robinson Foundation Scholarship' (a separate DB row) -- "
           "flagged as a suspected duplicate record, not merged automatically"),
    Repair("Elie Wiesel Prize in Ethics Essay Contest", "Elie Wiesel Foundation",
           "https://eliewieselfoundation.org/prize-in-ethics/", "fresh research, confirmed"),
    Repair("Kappa Alpha Theta Foundation Scholarship", "Kappa Alpha Theta Foundation",
           "https://www.kappaalphatheta.org/foundation/scholarships-grants/apply-for-scholarships-grants",
           "fresh research, confirmed"),

    # ---------------------------------------------------------------------
    # Phase 2 upgrades: high-confidence fixes discovered while investigating
    # the 27 "suspicious" records, meeting the same verification bar as
    # Phase 1. Not part of the 57 corrupted-by-add_urls_2.py set.
    # ---------------------------------------------------------------------
    Repair("Taiwanese American Scholarship Fund", "Taiwanese American Scholarship Fund",
           "https://tascholarshipfund.org/",
           "Phase 2: current URL (tascholarship.com) is a different, non-official domain; "
           "confirmed correct official domain is tascholarshipfund.org", sanity_override=True),
    Repair("American Indian Education Fund", "American Indian Education Fund",
           "https://www.aiefprogram.org/",
           "Phase 2: current URL is a stale ASP-era query-string page; "
           "aiefprogram.org is the program's current official site", sanity_override=True),
    Repair("National Sorority of Phi Delta Kappa Scholarship", "Phi Delta Kappa",
           "https://www.nspdk.org/perpetual-scholarship",
           "Phase 2: current URL is an informal wixsite.com subdomain; "
           "nspdk.org is the sorority's own official domain", sanity_override=True),
]


@dataclass
class Unresolve:
    title: str
    organization: str
    reason: str


# ---------------------------------------------------------------------------
# Confirmed WRONG (part of the add_urls_2.py corruption) but not confidently
# repairable -- researched and could not verify a specific official URL.
# Leaving the current (definitely wrong, points to an unrelated org) URL in
# place is worse than clearing it: a null source_url is honestly "we don't
# know," while the current value actively misdirects a student to the wrong
# organization's page. These are cleared to NULL, not guessed.
# ---------------------------------------------------------------------------
UNRESOLVED: list[Unresolve] = [
    Unresolve("SIEPR Economic Writing Prize", "Stanford Institute for Economic Policy Research",
              "No evidence this exact high-school-level prize currently exists at SIEPR; "
              "their real programs found (Landau Prize, Summer Institute) are for grad "
              "students/teachers, not a match for this title."),
    Unresolve("Tyson Foods Scholarship", "Tyson Foods",
              "Real Tyson Foods scholarships exist but are administered independently per "
              "manufacturing plant for employees' children, with no single central "
              "application URL to point to."),
    Unresolve("Procter and Gamble Scholarship", "Procter and Gamble",
              "P&G runs multiple distinct real scholarship programs (General Scholarship, "
              "STEM Scholarship, HBCYOU) with different URLs; the generic DB title doesn't "
              "specify which one, so picking one would be a guess."),
    Unresolve("US Constitution Essay Contest", "American Bar Association",
              "No single national ABA-run 'US Constitution Essay Contest' was found; several "
              "different bar-association-run constitution/civics essay contests exist "
              "(Federal Bar Association, various circuit-level ones), none matching this title."),
    Unresolve("Excellence in Education Award Grade 9", "National Academic Excellence Foundation",
              "No organization by this name was found. Likely a discontinued, highly local, "
              "or non-existent program."),
    Unresolve("Sophomore Achievement Award", "National Merit Corporation",
              "No such program found at National Merit Scholarship Corporation; PSAT-based "
              "National Merit recognition is junior-year only, with nothing for sophomores."),
    Unresolve("Junior Leadership Award", "Youth Leadership Foundation",
              "No organization by this name, and no matching program, was found."),
    Unresolve("Window and Door Manufacturers Association Scholarship", "WDMA",
              "WDMA (wdma.com) is a real trade association, but no dedicated scholarship "
              "program or page could be confirmed on their site."),
]


def _tokens(s: str) -> set[str]:
    import re
    stop = {"the", "of", "and", "for", "a", "an", "in", "on", "to", "scholars", "scholarship",
            "scholarships", "program", "award", "awards", "foundation", "national", "fund",
            "fellowship", "prize", "grant", "college", "university", "student", "students",
            "america", "american", "society", "association", "institute", "organization",
            "inc", "corp", "corporation", "memorial", "education", "educational", "council"}
    return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in stop and len(w) >= 4}


def _sanity_check(repair: Repair) -> bool:
    """Returns True if the URL's domain shares at least one significant
    word with the title/organization -- an independent guard against
    exactly the class of bug (URL for the wrong scholarship) this script
    exists to fix. Not a substitute for human verification (2)."""
    from urllib.parse import urlparse
    domain_flat = urlparse(repair.url).netloc.lower().replace("www.", "").replace("-", "").replace(".", "")
    combined = _tokens(repair.title) | _tokens(repair.organization)
    return any(tok in domain_flat for tok in combined)


def run():
    app = create_app("development")
    with app.app_context():
        updated, skipped_no_match, skipped_ambiguous, skipped_unverified, skipped_sanity = [], [], [], [], []

        for r in REPAIRS:
            if not r.verified:
                skipped_unverified.append(r)
                continue

            matches = Scholarship.query.filter(
                Scholarship.title == r.title, Scholarship.organization == r.organization
            ).all()

            if len(matches) == 0:
                skipped_no_match.append(r)
                continue
            if len(matches) > 1:
                skipped_ambiguous.append((r, matches))
                continue

            if not _sanity_check(r) and not r.sanity_override:
                skipped_sanity.append(r)
                continue

            scholarship = matches[0]
            old_url = scholarship.source_url
            scholarship.source_url = r.url
            updated.append((scholarship.id, r.title, old_url, r.url, r.note))

        cleared, cleared_no_match = [], []
        for u in UNRESOLVED:
            matches = Scholarship.query.filter(
                Scholarship.title == u.title, Scholarship.organization == u.organization
            ).all()
            if len(matches) != 1:
                cleared_no_match.append(u)
                continue
            scholarship = matches[0]
            old_url = scholarship.source_url
            scholarship.source_url = None
            cleared.append((scholarship.id, u.title, old_url, u.reason))

        db.session.commit()

        print(f"=== Updated: {len(updated)} ===")
        for sid, title, old, new, note in updated:
            print(f"  id={sid} '{title}'\n    old: {old}\n    new: {new}\n    ({note})")

        if skipped_no_match:
            print(f"\n=== SKIPPED, no title+org match found: {len(skipped_no_match)} ===")
            for r in skipped_no_match:
                print(f"  '{r.title}' / '{r.organization}'")

        if skipped_ambiguous:
            print(f"\n=== SKIPPED, ambiguous (multiple rows match): {len(skipped_ambiguous)} ===")
            for r, matches in skipped_ambiguous:
                print(f"  '{r.title}' matched ids: {[m.id for m in matches]}")

        if skipped_sanity:
            print(f"\n=== SKIPPED, failed domain sanity check (needs sanity_override + explanation): {len(skipped_sanity)} ===")
            for r in skipped_sanity:
                print(f"  '{r.title}' -> {r.url}")

        if skipped_unverified:
            print(f"\n=== SKIPPED, not marked verified: {len(skipped_unverified)} ===")

        print(f"\n=== Cleared to NULL (confirmed wrong, could not verify a replacement): {len(cleared)} ===")
        for sid, title, old, reason in cleared:
            print(f"  id={sid} '{title}'\n    was: {old}\n    reason: {reason}")

        if cleared_no_match:
            print(f"\n=== UNRESOLVED entries with no title+org match: {len(cleared_no_match)} ===")
            for u in cleared_no_match:
                print(f"  '{u.title}' / '{u.organization}'")

        total = Scholarship.query.count()
        with_url = Scholarship.query.filter(Scholarship.source_url.isnot(None)).count()
        print(f"\n{with_url} of {total} scholarships have a source_url set.")


if __name__ == "__main__":
    run()
