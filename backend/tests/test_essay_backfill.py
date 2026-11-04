"""Classifier behind the card's "Essay required" / "No essay" tag."""

from scraper.essay_backfill import classify


def test_essay_with_requirement_language():
    assert classify("Applicants must submit a 500 word essay on leadership.") is True
    assert classify("Write an essay, maximum 800 words.") is True


def test_title_essay_contest():
    assert classify("Enter now", title="Americanism Essay Contest") is True


def test_explicit_no_essay():
    assert classify("This phase requires no essays, no transcript.") is False
    assert classify("No essay required. Enter in two minutes.") is False
    assert classify("$1,000 no essay scholarship for seniors") is False


def test_nav_links_and_stray_mentions_are_unclear():
    assert classify("Browse no essay scholarships | Scholarships by major") is None
    assert classify("Read our latest book review essay on the blog") is None
    assert classify("An optional essay may strengthen your application") is None
    assert classify("Award of $2,000 for graduating seniors") is None
