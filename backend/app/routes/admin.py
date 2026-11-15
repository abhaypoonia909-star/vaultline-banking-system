from flask import Blueprint, jsonify

from app.security.decorators import admin_required
from app.services.account_service import deactivate_account, list_all_accounts
from app.services.security_service import admin_overview

bp = Blueprint("admin", __name__)


@bp.get("/dashboard")
@admin_required
def dashboard(_user):
    return jsonify(admin_overview())


@bp.get("/accounts")
@admin_required
def accounts(_user):
    return jsonify({"accounts": list_all_accounts()})


@bp.delete("/accounts/<int:account_id>")
@admin_required
def remove_account(_user, account_id):
    account = deactivate_account(account_id)
    return jsonify(
        {
            "message": "Account deactivated",
            "account_id": account.id,
            "account_number": account.account_number,
        }
    )
