from flask import Blueprint, jsonify

from app.models import Transaction
from app.security.decorators import login_required
from app.security.validators import parse_body
from app.services.account_service import (
    balance_summary,
    create_account,
    get_account_for_user,
    list_accounts,
)

bp = Blueprint("accounts", __name__)


@bp.get("")
@login_required
def accounts(user):
    return jsonify(list_accounts(user))


@bp.post("")
@login_required
def open_account(user):
    account = create_account(user, parse_body())
    return jsonify({"account": account.to_dict()}), 201


@bp.get("/balance")
@login_required
def balance(user):
    return jsonify(balance_summary(user))


@bp.get("/<int:account_id>")
@login_required
def account_detail(user, account_id):
    account = get_account_for_user(user, account_id)
    transactions = (
        Transaction.query.filter_by(account_id=account.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )
    return jsonify(
        {
            "account": account.to_dict(),
            "transactions": [item.to_dict() for item in transactions],
        }
    )
