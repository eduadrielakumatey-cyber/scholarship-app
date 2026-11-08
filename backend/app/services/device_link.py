"""
app/services/device_link.py
------------------------------
Short one-time codes that move a profile to another device, since a
device account has no email or password to log in with.

Codes are 8 characters from a 31-letter alphabet with look-alikes removed
(no 0/O, 1/I/L), about 40 bits: guessing one inside its 15-minute window
isn't practical. Only a SHA-256 hash is stored, so a database leak doesn't
hand out live codes.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
CODE_LIFETIME = timedelta(minutes=15)


def new_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def display(code: str) -> str:
    """K7QP4M2X -> K7QP-4M2X, easier to read out and type."""
    return f"{code[:4]}-{code[4:]}"


def normalize(raw) -> str:
    """Accepts what people actually type: lower case, spaces, dashes."""
    return "".join(ch for ch in str(raw or "").upper() if ch.isalnum())


def hash_code(code: str) -> str:
    return hashlib.sha256(normalize(code).encode("ascii", "ignore")).hexdigest()


def is_usable(link, now: datetime | None = None) -> bool:
    now = now or datetime.utcnow()
    return link is not None and link.used_at is None and link.expires_at > now
