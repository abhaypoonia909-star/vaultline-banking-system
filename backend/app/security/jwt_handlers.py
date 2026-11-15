from flask import jsonify

from app.extensions import db
from app.models import TokenBlocklist


def register_jwt_handlers(jwt):
    @jwt.token_in_blocklist_loader
    def token_revoked(_header, payload):
        jti = payload.get("jti")
        if not jti:
            return True
        return TokenBlocklist.query.filter_by(jti=jti).first() is not None

    @jwt.expired_token_loader
    def expired(_header, _payload):
        return jsonify({"error": "Session expired. Please sign in again."}), 401

    @jwt.invalid_token_loader
    def invalid(_reason):
        return jsonify({"error": "Invalid session. Please sign in again."}), 401

    @jwt.unauthorized_loader
    def missing(_reason):
        return jsonify({"error": "Authentication required"}), 401

    @jwt.revoked_token_loader
    def revoked(_header, _payload):
        return jsonify({"error": "Session ended. Please sign in again."}), 401

    @jwt.user_lookup_error_loader
    def missing_user(_header, _payload):
        db.session.rollback()
        return jsonify({"error": "Authentication required"}), 401
