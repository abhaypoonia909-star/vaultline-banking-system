import os
import shutil
import uuid
from pathlib import Path

from sqlalchemy.pool import NullPool

from app import create_app
from config import ProductionConfig, normalize_database_url

INSTANCE_ROOT = Path(__file__).resolve().parents[1] / "instance"


def _writable_instance_dir():
    INSTANCE_ROOT.mkdir(parents=True, exist_ok=True)
    path = INSTANCE_ROOT / f"vercel-test-{uuid.uuid4().hex}"
    path.mkdir()
    return path


def _vercel_production_env(monkeypatch, instance_dir, database_url):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("INSTANCE_PATH", str(instance_dir))
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTO_CREATE_TABLES", "0")
    monkeypatch.setenv("AUTO_SEED_ADMIN", "0")
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "production-secret-value-32-chars-min")
    monkeypatch.setattr(ProductionConfig, "JWT_SECRET_KEY", "production-jwt-secret-value-32-chars")
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", normalize_database_url(database_url))
    monkeypatch.setattr(ProductionConfig, "AUTO_CREATE_TABLES", False)
    monkeypatch.setattr(ProductionConfig, "AUTO_SEED_ADMIN", False)


def test_vercel_instance_directory_is_writable(monkeypatch):
    instance_dir = _writable_instance_dir()
    try:
        _vercel_production_env(
            monkeypatch,
            instance_dir,
            "postgres://dbuser:placeholder@db.internal:5432/banking",
        )

        application = create_app("production")
        resolved = Path(application.instance_path)

        assert resolved == instance_dir.resolve()
        assert resolved.is_dir()
        assert os.access(resolved, os.W_OK)

        probe = resolved / "write-check"
        probe.write_text("ok", encoding="utf-8")
        assert probe.read_text(encoding="utf-8") == "ok"

        uri = str(application.config["SQLALCHEMY_DATABASE_URI"])
        assert uri.startswith("postgresql+psycopg2://")
        assert "sqlite" not in uri
        assert application.config["AUTO_CREATE_TABLES"] is False
        assert application.config["PRODUCTION"] is True
        assert application.config["SQLALCHEMY_ENGINE_OPTIONS"].get("poolclass") is NullPool
        assert "/api/health" in {rule.rule for rule in application.url_map.iter_rules()}
    finally:
        shutil.rmtree(instance_dir, ignore_errors=True)


def test_vercel_production_still_rejects_sqlite(monkeypatch):
    instance_dir = _writable_instance_dir()
    try:
        _vercel_production_env(monkeypatch, instance_dir, "sqlite:///banking.db")
        try:
            create_app("production")
        except RuntimeError as exc:
            assert "PostgreSQL" in str(exc)
            return
        raise AssertionError("production startup must reject SQLite")
    finally:
        shutil.rmtree(instance_dir, ignore_errors=True)


def test_local_testing_keeps_default_instance_path(app):
    assert os.getenv("VERCEL") in (None, "")
    assert Path(app.instance_path).name != "vaultline-instance"
    assert "sqlite" in str(app.config["SQLALCHEMY_DATABASE_URI"])
    assert app.config["PRODUCTION"] is False
