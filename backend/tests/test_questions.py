"""
tests/test_questions.py
--------------------------
Copying a scholarship's application questions from its official page.
Pure functions, tested on small HTML/text samples (no network, no DB).

Run with:
    cd backend
    pytest tests/test_questions.py
"""

from app.services.questions import build, classify, from_html, requirement_question

PAGE = """
<dl><dt>Supplemental Questions</dt><dd><ol>
<li class="js-question">Are you a graduate of Allegany High School?</li>
<li class="js-question">Do you intend to transfer to Frostburg State University? If so, please explain:</li>
<li class="js-question">Please describe your career goals in 250 words or less.</li>
<li class="js-question">Please upload an updated PDF version of your resume.</li>
<li class="hidden_list js-question">Please provide the name and email address of one STEM professional to complete an optional recommendation.</li>
<li class="hidden_list js-question">List all STEM courses you will take this year.</li>
<li class="normalize-list-item"><a class="js-show-all" href="#">Show 2 more</a></li>
</ol></dd></dl>
"""


def test_reads_every_question_including_hidden_ones():
    qs = from_html(PAGE)
    assert len(qs) == 6
    assert [q["kind"] for q in qs] == ["yesno", "yesno", "written", "upload", "reference", "short"]
    assert qs[1]["follow_up"] is True
    assert "follow_up" not in qs[0]
    assert qs[2]["word_limit"] == 250


def test_keys_are_stable_and_ignore_spacing():
    assert classify("Why  nursing?")["key"] == classify("Why nursing?")["key"]


def test_numbering_and_checkboxes():
    assert classify("6. Do you have a FAFSA on file?")["text"] == "Do you have a FAFSA on file?"
    assert classify("Please verify this is accurate by checking the box:")["kind"] == "yesno"


def test_essay_stated_in_the_description_becomes_the_question():
    text = (
        "This scholarship will be awarded to a deserving student who has met the following minimum "
        "qualifications: Full-time student, have at least a 2.0 GPA , and state financial need in "
        "essay on scholarship application. Continuation of scholarship is possible."
    )
    q = requirement_question(text)
    assert q["text"] == "State financial need in essay on scholarship application."
    assert q["kind"] == "written" and q["source"] == "requirements"


def test_build_adds_the_requirement_only_when_no_essay_question_exists():
    desc = "Must have a 2.0 GPA and state financial need in essay on scholarship application. Award $500"
    yes_no_only = '<ol><li class="js-question">Are you a resident of Allegany County?</li></ol>'
    qs = build(yes_no_only, desc, essay_required=True)
    assert qs[0]["source"] == "requirements" and len(qs) == 2
    assert build(yes_no_only, desc, essay_required=False) == from_html(yes_no_only)


def test_essay_in_description_is_kept_alongside_other_written_questions():
    # Real case: an Allegany listing asks "please explain how..." AND says
    # "state financial need in essay" in its description: two things to write.
    desc = "Full-time student and state financial need in essay on scholarship application. Award $500"
    page = '<ol><li class="js-question">If so, please explain how your time contributed to student life.</li></ol>'
    qs = build(page, desc, essay_required=True)
    assert [q["source"] for q in qs] == ["requirements", "supplemental"]
    # ...but not when a listed question already is the essay.
    essay_page = '<ol><li class="js-question">Write a 300-word essay on your goals.</li></ol>'
    assert [q["source"] for q in build(essay_page, desc, essay_required=True)] == ["supplemental"]
