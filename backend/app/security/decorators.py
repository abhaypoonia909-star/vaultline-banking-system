from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import User


def current_user():
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


def _guard(admin_only):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user or not user.is_active:
                return jsonify({"error": "Authentication required"}), 401
            if admin_only and user.role != "admin":
                return jsonify({"error": "Admin access required"}), 403
            return fn(user, *args, **kwargs)

        return wrapper

    return decorator


login_required = _guard(False)
admin_required = _guard(True)
