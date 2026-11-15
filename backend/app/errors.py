from flask import jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from app.extensions import db


class APIError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(err):
        db.session.rollback()
        return jsonify({"error": err.message}), err.status

    @app.errorhandler(IntegrityError)
    def handle_integrity(_err):
        db.session.rollback()
        return jsonify({"error": "That record already exists"}), 409

    @app.errorhandler(429)
    def handle_rate_limit(_err):
        return jsonify({"error": "Too many requests. Try again later."}), 429

    @app.errorhandler(HTTPException)
    def handle_http(err):
        return jsonify({"error": err.description or err.name}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        db.session.rollback()
        app.logger.exception("Unhandled error")
        payload = {"error": "Internal server error"}
        if app.config.get("TESTING"):
            payload["detail"] = str(err)
        return jsonify(payload), 500
