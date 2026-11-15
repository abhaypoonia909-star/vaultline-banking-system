import re

from flask import request

from app.errors import APIError

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PIN_RE = re.compile(r"^\d{4}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 .'\-]{1,79}$")


def parse_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError("JSON body required")
    return data


def validate_username(value):
    if not isinstance(value, str) or not USERNAME_RE.match(value.strip()):
        raise APIError("Username must be 3 to 32 letters, numbers, or underscores")
    return value.strip()


def validate_email(value):
    if not isinstance(value, str):
        raise APIError("A valid email is required")
    email = value.strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 255:
        raise APIError("A valid email is required")
    return email


def validate_name(value, field="name"):
    if not isinstance(value, str) or not NAME_RE.match(value.strip()):
        raise APIError(f"{field} must be 2 to 80 letters")
    return value.strip()


def validate_password(password, username=None):
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        raise APIError("Password must be 8 to 128 characters")
    if any(ord(char) < 32 for char in password):
        raise APIError("Password contains invalid characters")
    if username and password.lower() == username.lower():
        raise APIError("Password cannot match the username")
    return password


def validate_pin(pin):
    if isinstance(pin, int) and not isinstance(pin, bool):
        pin = f"{pin:04d}" if 0 <= pin <= 9999 else str(pin)
    if not isinstance(pin, str) or not PIN_RE.match(pin.strip()):
        raise APIError("PIN must be exactly 4 digits")
    return pin.strip()
