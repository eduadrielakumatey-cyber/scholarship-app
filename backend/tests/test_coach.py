"""
tests/test_coach.py
----------------------
Essay Coach: input handling, the request sent to Claude, and how replies
are cleaned up. The Anthropic client is replaced with a fake, so these run
without a network or an API key.

Run with:
    cd backend
    pytest tests/test_coach.py
"""

import json
from types import SimpleNamespace

import pytest

from app.services import coach

ESSAY = (
    "When my grandmother got sick, I started cooking dinner for my three younger brothers every night. "
    "At first I burned rice and forgot the salt, but by spring I could make a full meal in thirty minutes. "
    "Those nights taught me that taking care of people is a skill you practice, and it is why I want to study nursing."
)


def test_plain_text_strips_editor_html():
    html = "<p>Hello <strong>world</strong></p><ul><li>one</li><li>two &amp; three</li></ul>"
    assert coach.plain_text(html) == "Hello world\none\ntwo & three"


def test_too_short_or_too_long_essays_never_reach_the_api():
    with pytest.raises(coach.CoachError, match="at least"):
        coach.get_feedback("Too short.", None, None, None, api_key="k", model="m")
    with pytest.raises(coach.CoachError, match="reads up to"):
        coach.get_feedback("word " * 2000, None, None, None, api_key="k", model="m")


def test_user_message_wraps_essay_and_question_as_data():
    msg = coach.build_user_message(ESSAY, "Why nursing?", 250, "Example Scholarship (Example College)")
    assert "<question>Why nursing?</question>" in msg
    assert "<essay>\n" + ESSAY + "\n</essay>" in msg
    assert "Word limit: 250" in msg


def test_quotes_not_in_the_essay_are_dropped():
    fb = {
        "strengths": [{"quote": "I started cooking dinner", "why": "specific"}, {"quote": "made up words", "why": "x"}],
        "improvements": [{"quote": "invented quote", "issue": "i", "suggestion": "s"}],
    }
    out = coach.keep_real_quotes(fb, ESSAY)
    assert out["strengths"][0]["quote"] == "I started cooking dinner"
    assert out["strengths"][1]["quote"] == ""
    assert out["improvements"][0]["quote"] == ""


class FakeMessages:
    def __init__(self, reply, stop_reason="end_turn"):
        self.reply, self.stop_reason, self.calls = reply, stop_reason, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=self.reply)],
        )


def install_fake(monkeypatch, reply, stop_reason="end_turn"):
    import anthropic

    fake = FakeMessages(reply, stop_reason)
    monkeypatch.setattr(
        anthropic, "Anthropic",
        lambda **kw: SimpleNamespace(beta=SimpleNamespace(messages=fake), messages=fake),
    )
    return fake


GOOD_REPLY = json.dumps({
    "summary": "Strong, specific story.",
    "answers_question": {"verdict": "yes", "explanation": "Ties cooking to nursing."},
    "strengths": [{"quote": "I burned rice and forgot the salt", "why": "honest detail"}],
    "improvements": [{"quote": "taking care of people is a skill", "issue": "abstract", "suggestion": "show one night"}],
})


def test_request_uses_structured_output_feedback_rules_and_fallback(monkeypatch):
    fake = install_fake(monkeypatch, GOOD_REPLY)
    fb = coach.get_feedback(f"<p>{ESSAY}</p>", "Why nursing?", 250, "Example", api_key="k", model="claude-opus-5-5")
    call = fake.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert "never write the essay" in call["system"]
    assert call["fallbacks"] == "default"
    assert "<p>" not in call["messages"][0]["content"]  # plain text, not editor HTML
    assert fb["answers_question"]["verdict"] == "yes"
    assert fb["strengths"][0]["quote"] == "I burned rice and forgot the salt"


def test_refusal_and_garbled_replies_become_friendly_errors(monkeypatch):
    install_fake(monkeypatch, "", stop_reason="refusal")
    with pytest.raises(coach.CoachError, match="couldn't review"):
        coach.get_feedback(ESSAY, None, None, None, api_key="k", model="m")
    install_fake(monkeypatch, "not json")
    with pytest.raises(coach.CoachError, match="garbled"):
        coach.get_feedback(ESSAY, None, None, None, api_key="k", model="m")


def test_haiku_requests_leave_out_fallbacks(monkeypatch):
    # Haiku has no server-side fallback; sending the parameter would fail every request.
    fake = install_fake(monkeypatch, GOOD_REPLY)
    coach.get_feedback(ESSAY, "Why nursing?", None, None, api_key="k", model="claude-haiku-5-5")
    call = fake.calls[0]
    assert "fallbacks" not in call and "betas" not in call
    assert call["output_config"]["format"]["type"] == "json_schema"
