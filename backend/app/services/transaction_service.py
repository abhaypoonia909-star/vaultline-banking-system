from decimal import Decimal

from sqlalchemy import func
from werkzeug.security import check_password_hash

from app.errors import APIError
from app.extensions import db
from app.models import BankAccount, Transaction
from app.money import as_decimal, money_str
from app.security.validators import validate_pin
from app.services.account_service import get_account_for_user
from app.timeutil import utcnow

MAX_TRANSACTION = Decimal("1000000.00")


def parse_amount(value):
    if isinstance(value, bool) or value is None:
        raise APIError("Enter a valid amount")
    try:
        amount = as_decimal(value)
    except ValueError:
        raise APIError("Enter a valid amount")
    if amount <= 0:
        raise APIError("Amount must be greater than zero")
    if amount > MAX_TRANSACTION:
        raise APIError("Amount exceeds the per-transaction limit")
    return amount


def _description(payload, fallback):
    note = payload.get("description")
    if isinstance(note, str) and note.strip():
        return note.strip()[:160]
    return fallback


def move_money(user, payload, txn_type):
    if txn_type not in {"deposit", "withdrawal"}:
        raise APIError("Unknown transaction type")
    amount = parse_amount(payload.get("amount"))
    pin = validate_pin(payload.get("pin"))
    try:
        account_id = int(payload.get("account_id"))
    except (TypeError, ValueError):
        raise APIError("Account not found", 404)

    query = BankAccount.query.filter_by(id=account_id, is_active=True)
    if db.engine.dialect.name == "postgresql":
        query = query.with_for_update()
    account = query.one_or_none()
    if not account or account.user_id != user.id:
        raise APIError("Account not found", 404)
    if not check_password_hash(account.pin_hash, pin):
        raise APIError("Invalid PIN", 403)

    balance = as_decimal(account.balance)
    if txn_type == "withdrawal" and amount > balance:
        raise APIError("Insufficient funds")

    if txn_type == "deposit":
        balance += amount
        description = _description(payload, "Deposit")
    else:
        balance -= amount
        description = _description(payload, "Withdrawal")

    account.balance = balance
    transaction = Transaction(
        account_id=account.id,
        user_id=user.id,
        txn_type=txn_type,
        amount=amount,
        balance_after=balance,
        description=description,
        created_at=utcnow(),
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction, account


def _filters(user, account_id):
    filters = [Transaction.user_id == user.id]
    if account_id not in (None, ""):
        account = get_account_for_user(user, account_id)
        filters.append(Transaction.account_id == account.id)
    return filters


def _sum(filters, txn_type):
    total = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(*filters, Transaction.txn_type == txn_type)
        .scalar()
    )
    return money_str(total or 0)


def transaction_history(user, account_id=None, limit=50):
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 50
    limit = min(max(limit, 1), 200)
    filters = _filters(user, account_id)
    rows = (
        Transaction.query.filter(*filters)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )
    count = db.session.query(func.count(Transaction.id)).filter(*filters).scalar() or 0
    return {
        "transactions": [row.to_dict() for row in rows],
        "totals": {
            "deposits": _sum(filters, "deposit"),
            "withdrawals": _sum(filters, "withdrawal"),
            "count": int(count),
        },
    }
