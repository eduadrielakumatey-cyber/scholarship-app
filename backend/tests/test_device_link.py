"""
tests/test_device_link.py
----------------------------
The one-time codes that move a profile to another device. The helpers
are pure, so (per this project's DB-free testing convention) they're
tested without a database.

Run with:
    cd backend
    pytest tests/test_device_link.py
"""

from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services import device_link as dl


def test_codes_are_8_unambiguous_characters():
    codes = {dl.new_code() for _ in range(500)}
    assert len(codes) == 500  # no repeats in a small sample
    for code in codes:
        assert len(code) == dl.CODE_LENGTH
        assert set(code) <= set(dl.ALPHABET)
        assert not set(code) & set("0O1IL")


def test_display_and_normalize_round_trip():
    assert dl.display("K7QP4M2X") == "K7QP-4M2X"
    assert dl.normalize("k7qp-4m2x") == "K7QP4M2X"
    assert dl.normalize("  K7QP 4M2X ") == "K7QP4M2X"
    assert dl.normalize(None) == ""


def test_hash_ignores_formatting_but_not_content():
    assert dl.hash_code("K7QP-4M2X") == dl.hash_code("k7qp4m2x")
    assert dl.hash_code("K7QP4M2X") != dl.hash_code("K7QP4M2Y")
    assert len(dl.hash_code("K7QP4M2X")) == 64


def test_usable_only_when_unused_and_unexpired():
    now = datetime(2026, 11, 8, 12, 0)
    fresh = SimpleNamespace(used_at=None, expires_at=now + timedelta(minutes=5))
    expired = SimpleNamespace(used_at=None, expires_at=now - timedelta(seconds=1))
    used = SimpleNamespace(used_at=now, expires_at=now + timedelta(minutes=5))
    assert dl.is_usable(fresh, now)
    assert not dl.is_usable(expired, now)
    assert not dl.is_usable(used, now)
    assert not dl.is_usable(None, now)
