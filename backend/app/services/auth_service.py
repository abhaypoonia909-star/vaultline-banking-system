from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token, get_jwt
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import APIError
from app.extensions import db
from app.http import client_ip
from app.models import LoginAttempt, SecurityLog, TokenBlocklist, User
from app.security.validators import validate_email, validate_name, validate_password, validate_username
from app.timeutil import utcnow

FAILURE_WINDOW = timedelta(minutes=15)
FAILURE_THRESHOLD = 5


def create_user(username, email, full_name, password, role="user"):
    if role not in {"user", "admin"}:
        raise APIError("Invalid role")
    username = validate_username(username)
    email = validate_email(email)
    full_name = validate_name(full_name, "Full name")
    password = validate_password(password, username)

    if User.query.filter(func.lower(User.username) == username.lower()).first():
        raise APIError("Username is already registered", 409)
    if User.query.filter(func.lower(User.email) == email.lower()).first():
        raise APIError("Email is already registered", 409)

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def _safe_username(username):
    if not isinstance(username, str):
        return "unknown"
    cleaned = "".join(char for char in username if char.isalnum() or char == "_")[:32]
    return cleaned.lower() or "unknown"


def _record_attempt(username, user, success, simulation=False):
    attempt = LoginAttempt(
        username=_safe_username(username),
        user_id=user.id if user else None,
        success=success,
        ip_address=client_ip(),
        is_simulation=simulation,
        created_at=utcnow(),
    )
    db.session.add(attempt)
    db.session.flush()
    return attempt


def _alert_repeated_failures(username, user):
    window_start = utcnow() - FAILURE_WINDOW
    safe_name = _safe_username(username)
    count = LoginAttempt.query.filter(
        LoginAttempt.username == safe_name,
        LoginAttempt.success.is_(False),
        LoginAttempt.is_simulation.is_(False),
        LoginAttempt.created_at >= window_start,
    ).count()
    if count < FAILURE_THRESHOLD:
        return
    existing = SecurityLog.query.filter(
        SecurityLog.event_type == "repeated_login_failures",
        SecurityLog.user_id == (user.id if user else None),
        SecurityLog.created_at >= window_start,
        SecurityLog.message == f"Repeated failed logins detected for '{safe_name}'",
    ).first()
    if existing:
        return
    db.session.add(
        SecurityLog(
            event_type="repeated_login_failures",
            severity="warning",
            message=f"Repeated failed logins detected for '{safe_name}'",
            user_id=user.id if user else None,
            ip_address=client_ip(),
            details={"failed_attempts": count, "window_minutes": 15},
        )
    )


def register_user(payload):
    user = create_user(
        payload.get("username"),
        payload.get("email"),
        payload.get("full_name"),
        payload.get("password"),
        role="user",
    )
    db.session.add(
        SecurityLog(
            event_type="account_registered",
            severity="info",
            message=f"Customer '{user.username}' registered",
            user_id=user.id,
            ip_address=client_ip(),
        )
    )
    db.session.commit()
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return user, token


def authenticate(username, password):
    generic = APIError("Invalid username or password", 401)
    if not isinstance(username, str) or not isinstance(password, str):
        raise generic
    username = username.strip()
    if len(password) < 1 or len(password) > 128:
        _record_attempt(username, None, False)
        db.session.commit()
        raise generic

    user = User.query.filter(func.lower(User.username) == username.lower()).first()
    if not user or not user.is_active or not check_password_hash(user.password_hash, password):
        _record_attempt(username, user if user and user.is_active else None, False)
        _alert_repeated_failures(username, user if user and user.is_active else None)
        db.session.commit()
        raise generic

    _record_attempt(user.username, user, True)
    db.session.add(
        SecurityLog(
            event_type="login_success",
            severity="info",
            message=f"Login succeeded for '{user.username}'",
            user_id=user.id,
            ip_address=client_ip(),
        )
    )
    db.session.commit()
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return user, token


def change_password(user, current_password, new_password):
    if not isinstance(current_password, str) or not check_password_hash(user.password_hash, current_password):
        raise APIError("Current password is incorrect")
    new_password = validate_password(new_password, user.username)
    if check_password_hash(user.password_hash, new_password):
        raise APIError("New password must be different")
    user.password_hash = generate_password_hash(new_password)
    db.session.add(
        SecurityLog(
            event_type="password_changed",
            severity="info",
            message=f"Password changed for '{user.username}'",
            user_id=user.id,
            ip_address=client_ip(),
        )
    )
    db.session.commit()


def revoke_current_token():
    claims = get_jwt()
    jti = claims.get("jti")
    if not jti:
        raise APIError("Session could not be closed", 400)
    if TokenBlocklist.query.filter_by(jti=jti).first():
        return
    expires_at = None
    if claims.get("exp"):
        expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    db.session.add(TokenBlocklist(jti=jti, expires_at=expires_at))
    db.session.commit()
