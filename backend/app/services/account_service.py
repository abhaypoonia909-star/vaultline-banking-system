from decimal import Decimal

from sqlalchemy import func
from werkzeug.security import generate_password_hash

from app.errors import APIError
from app.extensions import db
from app.http import client_ip
from app.models import BankAccount
from app.money import as_decimal, money_str
from app.security.validators import validate_name, validate_pin
from app.services.security_service import write_log

MAX_ACCOUNTS_PER_USER = 10
MAX_OPENING_BALANCE = Decimal("10000000.00")


def generate_account_number():
    current = db.session.query(func.max(BankAccount.account_number)).scalar()
    if current and str(current).isdigit():
        return str(int(current) + 1).zfill(8)
    return "10000001"


def get_account_for_user(user, account_id, allow_admin=False):
    try:
        account_id = int(account_id)
    except (TypeError, ValueError):
        raise APIError("Account not found", 404)
    account = db.session.get(BankAccount, account_id)
    if not account or not account.is_active:
        raise APIError("Account not found", 404)
    if account.user_id != user.id and not (allow_admin and user.role == "admin"):
        raise APIError("Account not found", 404)
    return account


def list_accounts(user):
    accounts = (
        BankAccount.query.filter_by(user_id=user.id, is_active=True)
        .order_by(BankAccount.created_at.desc())
        .all()
    )
    total = sum((as_decimal(account.balance) for account in accounts), Decimal("0.00"))
    return {
        "accounts": [account.to_dict() for account in accounts],
        "count": len(accounts),
        "total_balance": money_str(total),
    }


def balance_summary(user):
    summary = list_accounts(user)
    return {
        "total_balance": summary["total_balance"],
        "accounts": [
            {
                "id": item["id"],
                "account_number": item["account_number"],
                "balance": item["balance"],
            }
            for item in summary["accounts"]
        ],
    }


def create_account(user, payload):
    active_count = BankAccount.query.filter_by(user_id=user.id, is_active=True).count()
    if active_count >= MAX_ACCOUNTS_PER_USER:
        raise APIError("Account limit reached")

    holder_name = validate_name(payload.get("holder_name"), "Account name")
    pin = validate_pin(payload.get("pin"))
    try:
        opening = as_decimal(payload.get("initial_balance", "0"))
    except ValueError:
        raise APIError("Enter a valid opening balance")
    if opening < 0:
        raise APIError("Opening balance cannot be negative")
    if opening > MAX_OPENING_BALANCE:
        raise APIError("Opening balance exceeds the allowed limit")

    account = BankAccount(
        user_id=user.id,
        account_number=generate_account_number(),
        holder_name=holder_name,
        balance=opening,
        pin_hash=generate_password_hash(pin),
    )
    db.session.add(account)
    db.session.flush()
    write_log(
        event_type="bank_account_created",
        severity="info",
        message=f"Account {account.account_number} opened",
        user_id=user.id,
        ip_address=client_ip(),
        details={"account_number": account.account_number},
    )
    db.session.commit()
    return account


def list_all_accounts():
    accounts = (
        BankAccount.query.filter_by(is_active=True)
        .order_by(BankAccount.created_at.desc())
        .all()
    )
    return [account.to_dict(include_owner=True) for account in accounts]


def deactivate_account(account_id):
    try:
        account_id = int(account_id)
    except (TypeError, ValueError):
        raise APIError("Account not found", 404)
    account = db.session.get(BankAccount, account_id)
    if not account or not account.is_active:
        raise APIError("Account not found", 404)
    account.is_active = False
    write_log(
        event_type="admin_account_removed",
        severity="warning",
        message=f"Account {account.account_number} was deactivated",
        user_id=account.user_id,
        ip_address=client_ip(),
        details={"account_number": account.account_number, "account_id": account.id},
    )
    db.session.commit()
    return account
