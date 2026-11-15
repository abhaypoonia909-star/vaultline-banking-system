import os

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User
from app.security.validators import EMAIL_RE, USERNAME_RE


def ensure_admin():
    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower()
    full_name = os.getenv("ADMIN_FULL_NAME", "System Administrator").strip() or "System Administrator"

    if not username or not password:
        return False
    if not USERNAME_RE.match(username) or len(password) < 8 or len(password) > 128:
        return False
    if not EMAIL_RE.match(email):
        email = f"{username}@localhost"

    if User.query.filter_by(username=username).first():
        return False
    if User.query.filter_by(email=email).first():
        email = f"{username}@localhost"
        if User.query.filter_by(email=email).first():
            return False

    admin = User(
        username=username,
        email=email,
        full_name=full_name[:80],
        password_hash=generate_password_hash(password),
        role="admin",
    )
    db.session.add(admin)
    db.session.commit()
    return True
