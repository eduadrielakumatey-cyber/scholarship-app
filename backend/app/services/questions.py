"""
app/services/questions.py
----------------------------
The questions a scholarship's official application asks, so students can
answer them inside ScholarMatch (saved as they type) and paste them into
the official form.

Questions are copied word for word from the official page:
  - AcademicWorks portals list them under "Supplemental Questions"
    (<li class="js-question">), including ones folded behind "Show more".
  - When a listing requires an essay but states it in its description
    instead ("state financial need in essay on scholarship application"),
    that sentence becomes the question.

Each question gets a kind so the app can show the right input:
  written   -- an essay or describe/explain question (big box, word count)
  short     -- list / identify / provide a detail (small box)
  yesno     -- a yes/no question; follow_up=True when it adds "if so, explain"
  reference -- a recommender's name and contact details
  upload    -- a file they must upload on the official form
"""

import hashlib
import re

from bs4 import BeautifulSoup

UPLOAD = re.compile(r"\b(upload|attach|submit a (copy|pdf)|scan)\b", re.I)
REFERENCE = re.compile(r"(name and (e-?mail|contact|phone)|reference|recommend(ation|er)|letter of recommendation)", re.I)
YESNO_START = re.compile(r"^(are|do|did|have|has|is|will|were|was|can|would|does)\b", re.I)
FOLLOW_UP = re.compile(r"\b(if (so|yes)|please (explain|describe|identify|list)|explain|describe)\b", re.I)
WRITTEN = re.compile(
    r"\b(essay|describe|explain|discuss|tell us|why|how (will|has|have|do|did)|what (are|is|have|has) your|"
    r"reflect|in your own words|personal statement|share)\b",
    re.I,
)
SHORT = re.compile(r"^(list|identify|indicate|provide|please (list|identify|indicate|provide)|name|what is the|which)\b", re.I)
WORDS = re.compile(r"(\d{2,4})\s*(?:-|to)?\s*(\d{2,4})?\s*words?", re.I)
ESSAY_WORD = re.compile(r"\b(essay|personal statement|statement of)\b", re.I)
# Sentence ends: a period that isn't inside a number like "2.0", or ? / !.
SENTENCE_END = re.compile(r"(?<!\d)\.(?!\d)|[?!]")
CHECKBOX = re.compile(r"check(ing)? (the|this) box", re.I)
NUMBERING = re.compile(r"^\(?\d{1,2}[.)]\s+")


def question_key(text: str) -> str:
    return hashlib.sha1(" ".join(text.split()).lower().encode("utf-8")).hexdigest()[:12]


def classify(text: str) -> dict:
    t = NUMBERING.sub("", " ".join(text.split()))
    kind, follow_up = "written", False
    if CHECKBOX.search(t):
        kind = "yesno"
    elif ESSAY_WORD.search(t):
        # "Upload a 500-word essay..." still has to be written first.
        kind = "written"
    elif UPLOAD.search(t) and not WRITTEN.search(t.split(".")[0]):
        kind = "upload"
    elif REFERENCE.search(t) and not re.search(r"\b(describe|explain|discuss)\b", t, re.I):
        kind = "reference"
    elif YESNO_START.match(t):
        kind, follow_up = "yesno", bool(FOLLOW_UP.search(t))
    elif SHORT.match(t) and not re.search(r"\b(why|describe|explain|discuss)\b", t, re.I):
        kind = "short"
    elif not WRITTEN.search(t) and len(t) < 90:
        kind = "short"
    q = {"key": question_key(t), "text": t, "kind": kind, "source": "supplemental"}
    if follow_up:
        q["follow_up"] = True
    m = WORDS.search(t)
    if m and kind == "written":
        q["word_limit"] = int(m.group(2) or m.group(1))
    return q


def from_html(html: str) -> list[dict]:
    """Supplemental questions on an AcademicWorks opportunity page."""
    soup = BeautifulSoup(html or "", "html.parser")
    out, seen = [], set()
    for li in soup.select("li.js-question"):
        text = " ".join(li.get_text(" ").split())
        if len(text) < 4 or text.lower() in seen:
            continue
        seen.add(text.lower())
        out.append(classify(text))
    return out


def requirement_question(description_text: str) -> dict | None:
    """The sentence where a listing states its essay requirement, used as
    the question when there is no separate essay prompt."""
    # Takes the one clause that mentions the essay ("state financial need in
    # essay on scholarship application"), not the whole run-on eligibility
    # sentence it sits in.
    text = " ".join((description_text or "").split())
    for sentence in SENTENCE_END.split(text):
        if not ESSAY_WORD.search(sentence):
            continue
        clauses = [c.strip() for c in re.split(r"[;,](?![^()]*\))", sentence)]
        clause = next((c for c in clauses if ESSAY_WORD.search(c)), sentence.strip())
        clause = re.sub(r"^(and must|and|or|also|must)\s+", "", clause, flags=re.I).strip(" ,;:")
        if len(clause) < 10:
            continue
        clause = clause[0].upper() + clause[1:]
        if not clause.endswith((".", "?", "!")):
            clause += "."
        return {"key": question_key(clause), "text": clause, "kind": "written", "source": "requirements"}
    return None


def build(html: str, page_text: str, essay_required: bool | None) -> list[dict]:
    qs = from_html(html)
    if essay_required:
        # An essay named in the description ("state financial need in essay
        # on scholarship application") is its own question unless one of the
        # listed questions already is that essay.
        req = requirement_question(_listing_body(page_text))
        listed_essay = any(ESSAY_WORD.search(q["text"]) for q in qs)
        if req and not listed_essay and req["key"] not in {q["key"] for q in qs}:
            qs.insert(0, req)
    return qs


def _listing_body(page_text: str) -> str:
    """The listing's own description: drop site chrome before it and the
    award/deadline block and footer after it."""
    text = " ".join((page_text or "").split())
    return re.split(r"\bAward \$|Supplemental Questions|© 20\d\d", text)[0]
