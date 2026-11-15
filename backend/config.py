import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(url):
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


def _database_url(fallback_sqlite=True):
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return "sqlite:///banking.db" if fallback_sqlite else ""
    return normalize_database_url(url)


def _origins():
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [item.strip() for item in raw.split(",") if item.strip()]


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me-not-for-production-use")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-jwt-change-me-not-for-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRES_HOURS", "8")))
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = _origins()
    AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "1") == "1"
    AUTO_SEED_ADMIN = os.getenv("AUTO_SEED_ADMIN", "1") == "1"
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "1") == "1"
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    JSON_SORT_KEYS = False
    PRODUCTION = False
    TRUST_PROXY = False
    MAX_CONTENT_LENGTH = 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    PRODUCTION = True
    DEBUG = False
    TRUST_PROXY = os.getenv("TRUST_PROXY", "1") == "1"
    SQLALCHEMY_DATABASE_URI = _database_url(fallback_sqlite=False)


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-key-should-be-at-least-32-chars"
    JWT_SECRET_KEY = "test-jwt-secret-key-should-be-at-least-32"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTO_CREATE_TABLES = True
    AUTO_SEED_ADMIN = False
    RATELIMIT_ENABLED = False
    TRUST_PROXY = False
    CORS_ORIGINS = ["http://localhost:5173"]


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
