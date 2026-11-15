from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db, limiter

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
@limiter.exempt
def health():
    try:
        db.session.execute(text("SELECT 1"))
        database = "connected"
        status = "ok"
        code = 200
    except Exception:
        db.session.rollback()
        database = "unavailable"
        status = "degraded"
        code = 503
    return jsonify({"status": status, "database": database, "service": "banking-api"}), code
