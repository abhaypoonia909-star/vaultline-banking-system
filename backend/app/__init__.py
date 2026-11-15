import os

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy.pool import NullPool, StaticPool
from werkzeug.middleware.proxy_fix import ProxyFix

from app.errors import register_error_handlers
from app.extensions import db, jwt, limiter, migrate
from app.security.jwt_handlers import register_jwt_handlers
from app.services.bootstrap import ensure_admin
from config import config_by_name

VERCEL_INSTANCE_PATH = "/tmp/vaultline-instance"


def _writable_instance_path():
    if not os.getenv("VERCEL"):
        return None
    path = os.getenv("INSTANCE_PATH", VERCEL_INSTANCE_PATH)
    os.makedirs(path, exist_ok=True)
    return os.path.abspath(path)


def create_app(config_name=None):
    selected = config_name or os.getenv("APP_ENV", "development")
    if selected not in config_by_name:
        raise RuntimeError(f"Unknown APP_ENV '{selected}'")

    instance_path = _writable_instance_path()
    flask_kwargs = {}
    if instance_path is not None:
        flask_kwargs["instance_path"] = instance_path

    application = Flask(__name__, **flask_kwargs)
    application.config.from_object(config_by_name[selected])

    _configure_database_engine(application)
    _assert_production_safety(application)

    if application.config.get("TRUST_PROXY"):
        application.wsgi_app = ProxyFix(application.wsgi_app, x_for=1, x_proto=1)

    os.makedirs(application.instance_path, exist_ok=True)
    db.init_app(application)
    migrate.init_app(application, db)
    jwt.init_app(application)
    limiter.init_app(application)
    CORS(
        application,
        resources={r"/api/*": {"origins": application.config["CORS_ORIGINS"]}},
        allow_headers=["Authorization", "Content-Type"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    from app import models  # noqa: F401
    from app.routes.accounts import bp as accounts_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.health import bp as health_bp
    from app.routes.security import bp as security_bp
    from app.routes.transactions import bp as transactions_bp

    application.register_blueprint(health_bp)
    application.register_blueprint(auth_bp, url_prefix="/api/auth")
    application.register_blueprint(accounts_bp, url_prefix="/api/accounts")
    application.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    application.register_blueprint(admin_bp, url_prefix="/api/admin")
    application.register_blueprint(security_bp, url_prefix="/api/security")
    register_error_handlers(application)
    register_jwt_handlers(jwt)

    @application.get("/")
    @limiter.exempt
    def service_index():
        return jsonify(
            {
                "service": "Banking Management System API",
                "health": "/api/health",
            }
        )

    @application.cli.command("seed-admin")
    def seed_admin_command():
        """Create the admin user from ADMIN_USERNAME and ADMIN_PASSWORD."""
        created = ensure_admin()
        print("Admin user created." if created else "Admin user was not created.")

    if application.config.get("AUTO_CREATE_TABLES"):
        with application.app_context():
            try:
                db.create_all()
                if application.config.get("AUTO_SEED_ADMIN"):
                    ensure_admin()
            except Exception:
                application.logger.exception("Database initialization failed")
                db.session.rollback()

    return application


def _configure_database_engine(application):
    if application.config.get("TESTING"):
        application.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
        return
    if os.getenv("VERCEL"):
        application.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "poolclass": NullPool,
            "pool_pre_ping": True,
        }
        return
    if application.config.get("PRODUCTION"):
        application.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 280,
        }


def _assert_production_safety(application):
    if not application.config.get("PRODUCTION"):
        return
    secret = application.config.get("SECRET_KEY") or ""
    jwt_secret = application.config.get("JWT_SECRET_KEY") or ""
    db_uri = application.config.get("SQLALCHEMY_DATABASE_URI") or ""
    if (
        secret.startswith("dev-only")
        or jwt_secret.startswith("dev-only")
        or len(secret) < 16
        or len(jwt_secret) < 16
    ):
        raise RuntimeError("Set SECRET_KEY and JWT_SECRET_KEY before production startup")
    if not db_uri.startswith("postgresql"):
        raise RuntimeError("Production requires a PostgreSQL DATABASE_URL")


if os.getenv("FLASK_APP_AUTOLOAD", "1") == "1":
    app = create_app()
