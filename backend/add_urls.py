"""
add_urls.py
-----------
Adds real source URLs to all scholarships in the database.
Run with:
    docker compose exec backend python add_urls.py
"""

from app import create_app
from app.extensions import db
from app.models import Scholarship

URLS = {
    # NATIONAL
    "Coca-Cola Scholars Program": "https://www.coca-colascholarsfoundation.org/apply/",
    "Elks National Foundation Most Valuable Student": "https://www.elks.org/scholars/scholarships/mvs.cfm",
    "Prudential Spirit of Community Award": "https://spirit.prudential.com/",
    "National Merit Scholarship": "https://www.nationalmerit.org/s/1758/interior.aspx?sid=1758&gid=2&pgid=424",
    "Horatio Alger National Scholarship": "https://scholars.horatioalger.org/scholarships/",
    "Davidson Fellows Scholarship": "https://www.davidsongifted.org/fellows-scholarship/",
    "AXA Achievement Scholarship": "https://us.axa.com/axa-foundation/scholarship.html",
    "Burger King Scholars Program": "https://www.bkmclamorefoundation.org/what-we-do/bk-scholars/",
    "Do Something Award": "https://www.dosomething.org/us/scholarships",
    "Questbridge National College Match": "https://www.questbridge.org/high-school-students/national-college-match",
    "Jack Kent Cooke Foundation Scholarship": "https://www.jkcf.org/our-scholarships/college-scholarship-program/",
    "Posse Foundation Scholarship": "https://www.possefoundation.org/for-students",
    "Bonner Scholars Program": "https://bonner.org/scholars",
    "Comcast Leaders and Achievers": "https://corporate.comcast.com/values/comcast-nbcuniversal-foundation/leaders-and-achievers-scholarship-program",
    "VFW Voice of Democracy Scholarship": "https://www.vfw.org/community/youth-and-education/youth-scholarships",
    "Gloria Barron Prize for Young Heroes": "https://barronprize.org/",
    "Regeneron Science Talent Search": "https://www.societyforscience.org/regeneron-sts/",
    "Scholastic Art and Writing Awards": "https://www.artandwriting.org/",
    "YoungArts Foundation Award": "https://youngarts.org/apply/",
    "Ron Brown Scholar Program": "https://ronbrown.org/section/apply/program-description",

    # STEM
    "Google Generation Scholarship": "https://buildyourfuture.withgoogle.com/scholarships/google-scholarship-recipients",
    "Society of Women Engineers Scholarship": "https://swe.org/scholarships/",
    "SMART Scholarship for Service Program": "https://www.smartscholarship.org/smart",
    "Astronaut Scholarship Foundation": "https://astronautscholarship.org/scholarshipprogram.html",
    "Barry Goldwater Scholarship": "https://goldwaterscholarship.gov/",
    "Siemens Competition in Math Science and Technology": "https://www.siemens-foundation.org/",
    "AFCEA STEM Scholarship": "https://www.afcea.org/site/foundation/scholarships",
    "Amazon Future Engineer Scholarship": "https://www.amazonfutureengineer.com/scholarships",
    "Girls Who Code College Loop Scholarship": "https://girlswhocode.com/programs/college-loop",
    "National Science Foundation S-STEM Award": "https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=5257",
    "FIRST Robotics Scholarship": "https://www.firstinspires.org/alumni/scholarships",
    "Intel Science Talent Search": "https://www.societyforscience.org/intel-sts/",
    "CyberPatriot Scholarship": "https://www.uscyberpatriot.org/",
    "National Space Club Keynote Scholar": "https://www.spaceclub.org/scholarship/",
    "Microsoft Scholarship Program": "https://careers.microsoft.com/us/en/usscholarshipprogram",
    "Adobe Research Women in Technology Scholarship": "https://research.adobe.com/scholarship/",
    "Palantir Women in Technology Scholarship": "https://www.palantir.com/careers/students/scholarship/wit-north-america/",
    "Regeneron ISEF Award": "https://www.societyforscience.org/isef/",
    "NCWIT Aspirations in Computing Award": "https://www.aspirations.org/participate/high-school/award",
    "eCYBERMISSION Scholarship": "https://www.ecybermission.com/",
    "Society of Human Resource Management Scholarship": "https://www.shrm.org/foundation/ourwork/initiatives/Pages/Scholarship-Program.aspx",

    # ARTS
    "John Lennon Scholarship": "https://bmifoundation.org/programs/info/john_lennon_scholarships",
    "Doodle 4 Google Scholarship": "https://doodles.google/d4g/",
    "New York Times College Scholarship": "https://www.nytimes.com/scholarships",
    "Ayn Rand Essay Contest": "https://www.aynrand.org/students/essay-contests",
    "Worldstudio FOUNDATION Scholarship": "https://worldstudio.org/",
    "National Foundation for Advancement in the Arts Award": "https://www.nfaa.org/",
    "BMI Foundation Music Scholarship": "https://bmifoundation.org/programs",
    "American String Teachers Association Scholarship": "https://www.astastrings.org/Web/Resources/Scholarships_and_Awards/Web/Resources/ScholarshipsAwards.aspx",
    "L. Ron Hubbard Writers of the Future Contest": "https://www.writersofthefuture.com/enter-writer-contest/",
    "Duck Brand Duct Tape Stuck at Prom Scholarship": "https://www.duckbrand.com/stuck-at-prom",
    "National Orchestral Institute Scholarship": "https://noi.umd.edu/",
    "Congressional Art Competition Scholarship": "https://www.house.gov/educators-and-students/congressional-art-competition",

    # FIRST GENERATION
    "Dell Scholars Program": "https://www.dellscholars.org/scholarship/",
    "Thurgood Marshall College Fund Scholarship": "https://tmcf.org/students-alumni/scholarship/tmcf-scholarships/",
    "First in the Family Scholarship": "https://bold.org/scholarships/first-in-the-family-scholarship/",
    "OCA Gold Mountain First Generation Scholarship": "https://www.ocanational.org/scholarships",
    "GE-Reagan Foundation Scholarship": "https://www.reaganfoundation.org/education/scholarship-programs/ge-reagan-foundation-scholarship-program/",
    "Cargill Community Scholarship": "https://www.cargill.com/page/scholarships",
    "Sallie Mae Scholarship": "https://www.salliemae.com/college-planning/scholarships/",
    "Starbucks College Achievement Plan": "https://www.starbucks.com/careers/working-at-starbucks/education/",
    "Gates Scholarship": "https://www.thegatesscholarship.org/scholarship",

    # BLACK / AFRICAN AMERICAN
    "United Negro College Fund Scholarship": "https://uncf.org/scholarships",
    "Jackie Robinson Foundation Scholarship": "https://jackierobinson.org/apply/",
    "National Black MBA Association Scholarship": "https://nbmbaa.org/scholarships/",
    "Congressional Black Caucus Foundation Scholarship": "https://cbcfinc.org/programs/scholarships/",
    "National Society of Black Engineers Scholarship": "https://www.nsbe.org/scholarships",
    "Alpha Kappa Alpha Educational Advancement Scholarship": "https://akaeaf.org/scholarships",
    "Omega Psi Phi Scholarship": "https://oppf.org/scholarships/",
    "Black Nurses Association Scholarship": "https://www.nbna.org/schlrshp",
    "NAACP Legal Defense Fund Scholarship": "https://www.naacpldf.org/scholarships/",
    "Martin Luther King Jr. Scholarship": "https://apa1906.net/foundation/scholarships/",
    "Charles Drew Scholarship": "https://www.redcross.org/scholarships",

    # HISPANIC
    "Hispanic Scholarship Fund Award": "https://www.hsf.net/scholarship",
    "Hispanic Heritage Youth Award": "https://www.hispanicheritage.org/heritage-youth-awards/",
    "ALPFA Business Scholarship": "https://www.alpfa.org/page/ScholarshipProgram",
    "MALDEF Law School Scholarship": "https://www.maldef.org/leadership/scholarships/",
    "SHPE Foundation Scholarship": "https://www.shpe.org/page/scholarships",
    "National Hispanic Media Coalition Scholarship": "https://www.nhmc.org/scholarships/",
    "Hacu National Scholarship Program": "https://www.hacu.net/hacu/Scholarships.asp",
    "Congressional Hispanic Caucus Institute Scholarship": "https://chci.org/scholarships/",
    "LULAC National Scholarship Fund": "https://www.lulac.org/programs/education/scholarships/",
    "Hispanic Scholarship Fund First Generation Award": "https://www.hsf.net/scholarship",

    # ASIAN AMERICAN
    "Asian Pacific Islander American Scholarship Fund": "https://apiascholars.org/scholarship/apia-scholars/",
    "Asian American Journalists Association Scholarship": "https://www.aaja.org/programs-and-initiatives/scholarships-and-fellowships/",
    "Japanese American Citizens League Scholarship": "https://jacl.org/jacl-scholarships/",
    "Korean American Scholarship Foundation Award": "https://kasf.org/scholarships/",
    "Chinese American Citizens Alliance Scholarship": "https://www.cacanational.org/",
    "South Asian Bar Association Scholarship": "https://www.saba-inc.org/scholarships",
    "Filipino American League Scholarship": "https://www.fala.org/",
    "Taiwanese American Scholarship Fund": "https://tascholarship.com/",
    "OCA Asian Pacific American Advocates": "https://www.ocanational.org/scholarships",

    # NATIVE AMERICAN
    "American Indian College Fund Full Circle": "https://collegefund.org/students/scholarships/",
    "Catching the Dream STEM Scholarship": "https://catchingthedream.org/scholarship-programs/",
    "Native American Agriculture Fund Scholarship": "https://nativeamericanagriculturefund.org/scholarships/",
    "Bureau of Indian Education Scholarship": "https://www.bie.edu/topic/grants-scholarships",
    "American Indian Education Fund": "https://www.nativepartnership.org/site/PageServer?pagename=aief_home",
    "Sequoyah Fellowship Program": "https://www.aises.org/scholarships",

    # LGBTQ+
    "Point Foundation Scholarship": "https://pointfoundation.org/point-apply/apply-now/",
    "PFLAG National Scholarship": "https://pflag.org/scholarship",
    "Gamma Mu Foundation Scholarship": "https://gammamu.org/scholarship/",
    "Pride Foundation Scholarship": "https://pridefoundation.org/our-programs/scholarships/",
    "Equality Scholarship Collaborative": "https://www.equalityscholarship.org/",
    "Matthew Shepard Foundation Scholarship": "https://www.matthewshepard.org/our-work/scholarships/",
    "Transgender Scholarship and Education Legacy Fund": "https://tself.org/",

    # DISABILITY
    "American Council of the Blind Scholarship": "https://www.acb.org/scholarships",
    "National Federation of the Blind Scholarship": "https://nfb.org/programs-services/scholarships",
    "Lime Connect Scholarship": "https://www.limeconnect.com/opportunities/page/scholarships",
    "Google Lime Scholarship": "https://www.limeconnect.com/opportunities/page/scholarships",
    "National MS Society Scholarship": "https://www.nationalmssociety.org/Resources-Support/Find-Support/National-MS-Society-Scholarship-Program",
    "Millie Brother Scholarship for Children of Deaf Adults": "https://www.coda-international.org/scholarship",
    "Association on Higher Education and Disability Scholarship": "https://www.ahead.org/",

    # WOMEN
    "American Association of University Women Scholarship": "https://www.aauw.org/resources/programs/fellowships-grants/",
    "Zonta International Young Women in Public Affairs": "https://www.zonta.org/Global-Impact/Education/Young-Women-in-Public-Affairs-Award",
    "Soroptimist Live Your Dream Award": "https://www.soroptimist.org/our-work/live-your-dream-awards.html",
    "Society of Women Engineers Regional Scholarship": "https://swe.org/scholarships/",
    "Talbots Scholarship Foundation": "https://www.talbots.com/scholarship-foundation",

    # MILITARY / VETERAN
    "American Legion Scholarship": "https://www.legion.org/scholarships",
    "Scholarships for Military Children": "https://militaryscholar.org/smc/index.html",
    "Folds of Honor Scholarship": "https://foldsofhonor.org/scholarships/",
    "Gold Star Scholarship": "https://www.goldstarmoms.com/",
    "Pat Tillman Scholarship": "https://pattillmanfoundation.org/apply/",
    "National Military Family Association Scholarship": "https://www.militaryfamily.org/programs/scholarships/",
    "VFW Scout of the Year Scholarship": "https://www.vfw.org/community/youth-and-education/youth-scholarships",
    "American Legion Auxiliary Scholarship": "https://www.alaforveterans.org/scholarships/",
    "Folds of Honor Scholarship": "https://foldsofhonor.org/scholarships/",
    "Disabled American Veterans Scholarship": "https://www.dav.org/learn-more/scholarships/",

    # RURAL
    "National Rural Education Association Scholarship": "https://www.nrea.net/",
    "Agriculture Future of America Scholarship": "https://www.agfuture.org/scholarships/",
    "Farm Bureau Scholarship": "https://www.fb.org/land/scholarships",
    "4-H Youth Development Scholarship": "https://4-h.org/about/4-h-programs/",
    "FFA Scholarship Program": "https://www.ffa.org/participate/grants-and-scholarships/scholarships/",
    "Rural Health Care Provider Scholarship": "https://nhsc.hrsa.gov/scholarships",

    # COMMUNITY SERVICE
    "President's Volunteer Service Award": "https://presidentialserviceawards.gov/",
    "Rotary Foundation Scholarship": "https://www.rotary.org/en/our-programs/scholarships",
    "Key Club Scholarship": "https://www.keyclub.org/resources/scholarships/",
    "National Honor Society Scholarship": "https://www.nhs.us/students/nhs-scholarship/",
    "Spirit of Anne Frank Award": "https://annefrank.com/award/",
    "Youth Activism Project Scholarship": "https://youthactivismproject.org/",

    # SPORTS
    "Foot Locker Scholar Athletes Program": "https://www.footlocker.com/category/community/scholar-athletes.html",
    "ESPN Sports Humanitarian Award Scholarship": "https://www.espn.com/espn/story/_/id/sports-humanitarian-awards",
    "Women's Sports Foundation Scholarship": "https://www.womenssportsfoundation.org/programs/scholarships/",
    "National Strength and Conditioning Association Scholarship": "https://www.nsca.com/membership/scholarships/",

    # BUSINESS
    "DECA Scholarship": "https://www.deca.org/scholarships/",
    "Future Business Leaders of America Scholarship": "https://www.fbla-pbl.org/fbla/scholarships/",
    "Network for Teaching Entrepreneurship Award": "https://www.nfte.com/",
    "Junior Achievement Scholarship": "https://jausa.ja.org/dA/6d4ade4b52/file/JA%20Scholarships.pdf",
    "American Institute of Certified Public Accountants Scholarship": "https://www.aicpa.org/career/scholarships.html",

    # HEALTHCARE
    "National Health Service Corps Scholarship": "https://nhsc.hrsa.gov/scholarships",
    "Tylenol Future Care Scholarship": "https://www.tylenol.com/news/scholarship",
    "American Medical Association Foundation Scholarship": "https://www.ama-assn.org/about/ama-foundation/ama-foundation-scholarships",
    "National Student Nurses Association Scholarship": "https://www.nsna.org/scholarships-listing.html",
    "Health Professions Scholarship Program": "https://www.hpsp.usuhs.edu/",
    "American Dental Education Association Scholarship": "https://www.adea.org/GoDental/Money_Matters/Scholarships_and_Grants.aspx",
    "American Physical Therapy Association Scholarship": "https://www.apta.org/your-career/scholarships",

    # STATE
    "Maryland State Delegate Scholarship": "https://mhec.maryland.gov/preparing/Pages/FinancialAid/ProgramDescriptions/prog_delegate.aspx",
    "Maryland HOPE Scholarship": "https://mhec.maryland.gov/",
    "Cal Grant A": "https://www.csac.ca.gov/cal-grants",
    "TEXAS Grant": "https://www.highered.texas.gov/student-success-initiatives/financial-aid-programs/texas-grant/",
    "Terry Foundation Scholarship": "https://www.terryfoundation.org/scholarships",
    "New York State TAP Grant": "https://www.hesc.ny.gov/pay-for-college/financial-aid/types-of-financial-aid/grants/tap.html",
    "Florida Bright Futures Scholarship": "https://www.floridastudentfinancialaidsg.org/ssfad/bf/",
    "Illinois MAP Grant": "https://www.isac.org/students/during-college/types-of-financial-aid/grants/map/",
    "Pennsylvania State Grant": "https://www.pheaa.org/grants/state-grant-program/",
    "Georgia HOPE Scholarship": "https://www.gsfc.georgia.gov/hope",
    "Virginia Guaranteed Assistance Program": "https://www.schev.edu/index/students-and-parents/financial-aid/vgap",
    "Washington State Need Grant": "https://wsac.wa.gov/washington-state-need-grant",
    "Ohio College Opportunity Grant": "https://www.highered.ohio.gov/financial-aid-overview/grants-and-scholarships/ocog",
    "North Carolina Education Lottery Scholarship": "https://www.cfnc.org/pay-for-college/nc-financial-aid/nc-education-lottery-scholarship/",
    "Michigan Tuition Grant": "https://www.michigan.gov/mistudentaid/programs/tgp",
    "New Jersey Tuition Aid Grant": "https://www.hesaa.org/Pages/TAGHome.aspx",
    "Colorado Student Grant": "https://cdhe.colorado.gov/students/paying-for-college/financial-aid/grants",
    "Oregon Opportunity Grant": "https://oregonstudentaid.gov/grants-oregon-opportunity.aspx",
    "Minnesota State Grant": "https://www.ohe.state.mn.us/mPg.cfm?pageID=1878",
    "Wisconsin Higher Education Grant": "https://heab.state.wi.us/programs.html",
    "Indiana Frank O'Bannon Grant": "https://www.in.gov/che/4493.htm",
    "Arizona Leveraging Educational Assistance Partnership Grant": "https://students.asu.edu/financial-aid/grants/arizona-leveraging",
    "Tennessee Student Assistance Award": "https://www.tn.gov/tnstars/",

    # NO ESSAY
    "Niche 25000 Dollar Scholarship": "https://www.niche.com/colleges/scholarships/",
    "ScholarshipPoints Monthly Award": "https://www.scholarshippoints.com/",
    "Bold.org Monthly Scholarship": "https://bold.org/scholarships/",
    "Going Merry Matching Scholarship": "https://www.goingmerry.com/",
    "Unigo 10000 Scholarship": "https://www.unigo.com/scholarships/our-scholarships",
    "Cappex Easy College Money Scholarship": "https://www.cappex.com/scholarships",
    "Fastweb Scholarship Search Award": "https://www.fastweb.com/",
    "CollegeXpress Scholarship": "https://www.collegexpress.com/scholarships/",
    "Discover Student Loans Scholarship Award": "https://www.discover.com/student-loans/scholarships/",
    "Scholly Search Scholarship": "https://myscholly.com/",

    # NICHE
    "Vegetarian Resource Group Scholarship": "https://www.vrg.org/student/scholar.htm",
    "National Potato Council Scholarship": "https://www.nationalpotatocouncil.org/scholarship/",
    "Tall Clubs International Scholarship": "https://tall.org/tcif/",
    "Zombie Apocalypse Scholarship": "https://www.unigo.com/scholarships/our-scholarships/zombie-apocalypse-scholarship",
    "Stuck at Prom Duct Tape Scholarship": "https://www.duckbrand.com/stuck-at-prom",
    "Odenza Marketing Group Scholarship": "https://www.odenzascholarships.com/",

    # ENVIRONMENT
    "Brower Youth Award": "https://www.earthisland.org/index.php/aboutUs/browerYouthAwards",
    "EPA Environmental Youth Award": "https://www.epa.gov/students/presidents-environmental-youth-award",
    "National Garden Club Scholarship": "https://gardenclub.org/scholarships",
    "Youth Environmental Activist Scholarship": "https://environmentamerica.org/",

    # JOURNALISM
    "Robert F. Kennedy Journalism Award": "https://rfkhumanrights.org/work/journalism-award",
    "Hearst Journalism Scholarship": "https://www.hearstfdn.org/hearst-journalism/",
    "Society of Professional Journalists Scholarship": "https://www.spj.org/scholarships.asp",
    "National Press Club Scholarship": "https://www.press.org/programs/scholarships",
    "National Association of Black Journalists Scholarship": "https://www.nabj.org/page/scholinfo",
    "National Association of Hispanic Journalists Scholarship": "https://nahj.org/scholarships/",

    # PUBLIC SERVICE
    "Harry S Truman Scholarship": "https://www.truman.gov/",
    "Morris K Udall Scholarship": "https://www.udall.gov/OurPrograms/Scholarship/Scholarship.aspx",
    "National Security Agency Scholarship": "https://www.intelligencecareers.gov/nsa/nsastudents.html",
    "CIA Undergraduate Scholarship": "https://www.cia.gov/careers/student-opportunities/undergraduate-scholarship-program.html",
    "Boren Scholarship Program": "https://www.borenawards.org/",

    # PROFESSIONAL ORGS
    "American Chemical Society Scholars Program": "https://www.acs.org/content/acs/en/funding/scholarships-fellowships/acs-scholars.html",
    "American Meteorological Society Scholarship": "https://www.ametsoc.org/index.cfm/ams/education-careers/careers/scholarships-and-fellowships/",
    "American Nuclear Society Scholarship": "https://www.ans.org/honors/scholarships/",
    "Architecture Foundation Scholarship": "https://www.acsa-arch.org/programs-events/scholarships/",
    "American Welding Society Scholarship": "https://www.aws.org/aws-foundation/page/apply-for-a-scholarship",
    "National Restaurant Association Educational Foundation": "https://www.chooserestaurants.org/programs-and-scholarships/",
    "Society of Automotive Engineers Scholarship": "https://www.sae.org/participate/scholarships",
    "National Society of Professional Engineers Scholarship": "https://www.nspe.org/resources/students/scholarships",
    "American Institute of Chemical Engineers Scholarship": "https://www.aiche.org/community/awards/scholarships",
    "American Society of Civil Engineers Scholarship": "https://www.asce.org/career-growth/scholarships--fellowships",
    "American Society of Mechanical Engineers Scholarship": "https://www.asme.org/career-education/scholarships-grants",
    "Institute of Electrical and Electronics Engineers Scholarship": "https://www.ieee.org/membership/students/scholarships/index.html",
    "Water Environment Federation Scholarship": "https://www.wef.org/resources/for-students/scholarships/",
    "Geological Society of America Scholarship": "https://www.geosociety.org/gsa/grants/home.aspx",
    "Transportation Research Board Scholarship": "https://trb.org/",

    # UNION / CORPORATE
    "Walmart Associate Scholarship": "https://walmart.scholarsapply.org/",
    "Target Dependent Scholarship": "https://corporate.target.com/careers/scholarship",
    "Home Depot Scholarship": "https://homedepotfoundation.org/",
    "General Motors Foundation Scholarship": "https://www.gm.com/commitments/community.html",
    "Teamsters Scholarship": "https://teamster.org/benefits/scholarships/",
    "United Auto Workers Scholarship": "https://uaw.org/benefits/scholarships/",
    "AFSCME Family Scholarship": "https://www.afscme.org/union/education/scholarships",
    "SEIU Scholarship": "https://www.seiu.org/scholarships",
    "American Federation of Teachers Scholarship": "https://www.aft.org/scholarships",

    # MISC
    "National Italian American Foundation Scholarship": "https://www.niaf.org/programs/scholarships/",
    "Sons of Norway Foundation Scholarship": "https://www.sofn.com/foundation/scholarships/",
    "National Sorority of Phi Delta Kappa Scholarship": "https://npdkorg.wixsite.com/nspdk",
    "National Society Daughters of the American Revolution Scholarship": "https://www.dar.org/national-society/scholarships",
    "Phi Beta Kappa Scholarship": "https://www.pbk.org/Scholarship",
    "Alpha Phi Alpha Scholarship": "https://apa1906.net/foundation/scholarships/",
    "Black Girls Code Scholarship": "https://www.blackgirlscode.com/",
    "Codepath Tech Scholarship": "https://www.codepath.org/scholarships",
    "AI4ALL Open Minds Scholarship": "https://ai-4-all.org/open-minds/",
    "Lemelson MIT Student Prize": "https://lemelson.mit.edu/studentprize",
    "STEM Excellence Award for Underrepresented Students": "https://www.stemedcoalition.org/",
    "National Education Association Foundation Scholarship": "https://www.neafoundation.org/for-students/scholarships/",
    "Dollars for Scholars Community Award": "https://scholarshipamerica.org/dollarsforscholars/",
    "NSHSS Scholar Award": "https://www.nshss.org/scholarships/",
    "National Honor Society Scholarship": "https://www.nhs.us/students/nhs-scholarship/",
    "Phi Theta Kappa Foundation Scholarship": "https://www.ptk.org/ptk-scholarships/",
    "Elks State Scholarship": "https://www.elks.org/scholars/",
    "American Marketing Association Scholarship": "https://www.ama.org/scholarships/",
    "National Retail Federation Foundation Scholarship": "https://nrffoundation.org/scholarships",
    "Institute of Management Accountants Scholarship": "https://www.imanet.org/career-resources/ima-scholarships",
    "Public Relations Student Society of America Scholarship": "https://prssa.prsa.org/scholarships-competitions-and-awards/",
    "National Association of Realtors Scholarship": "https://www.nar.realtor/education/scholarships",
}


def run():
    app = create_app("development")
    with app.app_context():
        updated = 0
        not_found = 0
        for title, url in URLS.items():
            scholarship = Scholarship.query.filter(
                Scholarship.title.ilike(f"%{title[:30]}%")
            ).first()
            if scholarship:
                scholarship.source_url = url
                updated += 1
            else:
                not_found += 1
                print(f"Not found: {title}")
        db.session.commit()
        print(f"\nDone! Updated {updated} scholarships with URLs.")
        print(f"Not matched: {not_found}")

        with_url = Scholarship.query.filter(Scholarship.source_url != None).count()
        total = Scholarship.query.count()
        print(f"{with_url} of {total} scholarships now have a URL.")


if __name__ == "__main__":
    run()
