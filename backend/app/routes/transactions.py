from flask import Blueprint, jsonify, request

from app.security.decorators import login_required
from app.security.validators import parse_body
from app.services.transaction_service import move_money, transaction_history

bp = Blueprint("transactions", __name__)


@bp.post("/deposit")
@login_required
def deposit(user):
    transaction, account = move_money(user, parse_body(), "deposit")
    return jsonify({"transaction": transaction.to_dict(), "balance": account.to_dict()["balance"]}), 201


@bp.post("/withdraw")
@login_required
def withdraw(user):
    transaction, account = move_money(user, parse_body(), "withdrawal")
    return jsonify({"transaction": transaction.to_dict(), "balance": account.to_dict()["balance"]}), 201


@bp.get("/history")
@login_required
def history(user):
    return jsonify(
        transaction_history(
            user,
            account_id=request.args.get("account_id"),
            limit=request.args.get("limit", 50),
        )
    )
