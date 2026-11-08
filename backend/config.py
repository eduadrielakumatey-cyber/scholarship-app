"""
config.py
---------
Central place for all environment-driven configuration.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Shared settings for all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    # Bump whenever the Terms of Service or Privacy Policy materially change
    # (keep in sync with LEGAL_VERSION in frontend/src/legal/siteInfo.js).
    # Stored on each user at signup as a record of what they agreed to.
    TERMS_VERSION = "2026-11-08"

    # 🔥 FIX: NO FALLBACK DATABASE (prevents fake scholar_user issue)
    # Some hosts (Railway, Heroku) hand out DATABASE_URL with the old
    # `postgres://` scheme, which SQLAlchemy's psycopg2 dialect rejects --
    # normalize it to `postgresql://` before use. No-op for URLs that
    # already use the modern scheme (e.g. local dev).
    _database_url = os.environ.get("DATABASE_URL")
    if _database_url and _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173"
    ).split(",")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}