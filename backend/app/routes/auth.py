from flask import Blueprint, jsonify

from app.extensions import limiter
from app.security.decorators import login_required
from app.security.validators import parse_body
from app.services.auth_service import authenticate, change_password, register_user, revoke_current_token

bp = Blueprint("auth", __name__)


@bp.post("/register")
def register():
    user, token = register_user(parse_body())
    return jsonify({"access_token": token, "token_type": "Bearer", "user": user.to_dict()}), 201


@bp.post("/login")
@limiter.limit("5 per minute")
def login():
    payload = parse_body()
    user, token = authenticate(payload.get("username"), payload.get("password"))
    return jsonify({"access_token": token, "token_type": "Bearer", "user": user.to_dict()})


@bp.post("/logout")
@login_required
def logout(_user):
    revoke_current_token()
    return jsonify({"message": "Signed out"})


@bp.get("/me")
@login_required
def me(user):
    return jsonify({"user": user.to_dict()})


@bp.post("/change-password")
@login_required
def update_password(user):
    payload = parse_body()
    change_password(user, payload.get("current_password"), payload.get("new_password"))
    return jsonify({"message": "Password updated"})
