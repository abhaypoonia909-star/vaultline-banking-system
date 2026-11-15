from datetime import timedelta, timezone

from sqlalchemy import func
from werkzeug.security import check_password_hash

from app.errors import APIError
from app.extensions import db
from app.http import client_ip
from app.models import BankAccount, LoginAttempt, SecurityLog, Transaction, User
from app.money import money_str
from app.security.simulation import DEMO_GUESSES, MAX_DEMO_ATTEMPTS
from app.timeutil import iso, utcnow

ALERT_EVENTS = ("repeated_login_failures", "weak_password_detected")


def write_log(event_type, severity, message, user_id=None, ip_address=None, details=None):
    entry = SecurityLog(
        event_type=event_type,
        severity=severity,
        message=message[:500],
        user_id=user_id,
        ip_address=ip_address,
        details=details,
        created_at=utcnow(),
    )
    db.session.add(entry)
    return entry


def _scoped_attempts(user):
    query = LoginAttempt.query
    if user.role != "admin":
        query = query.filter(
            (LoginAttempt.user_id == user.id) | (LoginAttempt.username == user.username.lower())
        )
    return query


def _scoped_logs(user):
    query = SecurityLog.query
    if user.role != "admin":
        query = query.filter(SecurityLog.user_id == user.id)
    return query


def _count_pair(query):
    total = query.count()
    failed = query.filter(LoginAttempt.success.is_(False)).count()
    return total, failed, total - failed


def _daily_logins(user):
    start = utcnow() - timedelta(days=6)
    attempts = _scoped_attempts(user).filter(
        LoginAttempt.is_simulation.is_(False),
        LoginAttempt.created_at >= start,
    ).all()
    found = {}
    for attempt in attempts:
        created = attempt.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        key = created.astimezone(timezone.utc).date().isoformat()
        bucket = found.setdefault(
            key, {"date": key, "total": 0, "successful": 0, "failed": 0}
        )
        bucket["total"] += 1
        bucket["successful" if attempt.success else "failed"] += 1
    today = utcnow().date()
    return [
        found.get(
            (today - timedelta(days=offset)).isoformat(),
            {
                "date": (today - timedelta(days=offset)).isoformat(),
                "total": 0,
                "successful": 0,
                "failed": 0,
            },
        )
        for offset in range(6, -1, -1)
    ]


def security_overview(user):
    real_total, real_failed, real_success = _count_pair(
        _scoped_attempts(user).filter(LoginAttempt.is_simulation.is_(False))
    )
    sim_total, sim_failed, sim_success = _count_pair(
        _scoped_attempts(user).filter(LoginAttempt.is_simulation.is_(True))
    )
    logs = _scoped_logs(user)
    alerts = logs.filter(SecurityLog.event_type.in_(ALERT_EVENTS)).count()
    recent_logs = logs.order_by(SecurityLog.created_at.desc()).limit(50).all()
    recent_attempts = (
        _scoped_attempts(user).order_by(LoginAttempt.created_at.desc()).limit(50).all()
    )
    simulations = (
        logs.filter(SecurityLog.event_type == "brute_force_simulation")
        .order_by(SecurityLog.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "summary": {
            "total_attempts": real_total,
            "failed_attempts": real_failed,
            "successful_attempts": real_success,
            "simulated_attempts": sim_total,
            "simulated_failures": sim_failed,
            "simulated_matches": sim_success,
            "brute_force_alerts": alerts,
            "security_events": logs.count(),
        },
        "daily_logins": _daily_logins(user),
        "logs": [item.to_dict() for item in recent_logs],
        "attempts": [item.to_dict() for item in recent_attempts],
        "simulations": [item.to_dict() for item in simulations],
    }


def run_simulation(user, payload):
    if any(key in payload for key in ("passwords", "wordlist", "guesses")):
        raise APIError("Custom password lists are not accepted")
    if payload.get("acknowledge") is not True:
        raise APIError("Confirm this runs only against a local account in this application")

    attempts = payload.get("attempts", MAX_DEMO_ATTEMPTS)
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= MAX_DEMO_ATTEMPTS:
        raise APIError(f"attempts must be an integer from 1 to {MAX_DEMO_ATTEMPTS}")

    from app.services.account_service import get_account_for_user

    account = get_account_for_user(user, payload.get("account_id"), allow_admin=True)
    owner = account.owner
    if owner is None:
        raise APIError("Account not found", 404)

    started = utcnow()
    successful = 0
    failed = 0
    matched = False
    for candidate in DEMO_GUESSES[:attempts]:
        ok = check_password_hash(owner.password_hash, candidate)
        db.session.add(
            LoginAttempt(
                username=owner.username.lower(),
                user_id=owner.id,
                success=ok,
                ip_address=client_ip(),
                is_simulation=True,
                created_at=utcnow(),
            )
        )
        if ok:
            successful += 1
            matched = True
            break
        failed += 1

    finished = utcnow()
    repeated = failed >= 3
    details = {
        "account_number": account.account_number,
        "attempts_run": successful + failed,
        "failed_guesses": failed,
        "successful_guesses": successful,
        "weak_password_detected": matched,
        "repeated_failure_alert": repeated,
    }
    write_log(
        event_type="brute_force_simulation",
        severity="warning" if repeated else "info",
        message=f"Local brute-force simulation finished for account {account.account_number}",
        user_id=owner.id,
        ip_address=client_ip(),
        details=details,
    )
    if matched:
        write_log(
            event_type="weak_password_detected",
            severity="critical",
            message=(
                f"A common weak password matched the owner of account {account.account_number}. "
                "The password was not recorded."
            ),
            user_id=owner.id,
            ip_address=client_ip(),
            details={"account_number": account.account_number},
        )
    elif repeated:
        write_log(
            event_type="repeated_login_failures",
            severity="warning",
            message=f"Simulation recorded repeated failures for account {account.account_number}",
            user_id=owner.id,
            ip_address=client_ip(),
            details={"account_number": account.account_number, "failed_guesses": failed},
        )
    db.session.commit()
    return {
        "account_id": account.id,
        "account_number": account.account_number,
        "attempts_requested": attempts,
        "attempts_run": details["attempts_run"],
        "successful_guesses": successful,
        "failed_guesses": failed,
        "weak_password_detected": matched,
        "repeated_failure_alert": repeated,
        "started_at": iso(started),
        "finished_at": iso(finished),
        "message": "Local simulation finished. No password was disclosed.",
    }


def admin_overview():
    total_balance = (
        db.session.query(func.coalesce(func.sum(BankAccount.balance), 0))
        .filter(BankAccount.is_active.is_(True))
        .scalar()
    )
    deposits = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.txn_type == "deposit")
        .scalar()
    )
    withdrawals = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.txn_type == "withdrawal")
        .scalar()
    )
    since = utcnow() - timedelta(hours=24)
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(8).all()
    recent_alerts = (
        SecurityLog.query.filter(SecurityLog.severity.in_(("warning", "critical")))
        .order_by(SecurityLog.created_at.desc())
        .limit(8)
        .all()
    )
    return {
        "users": User.query.count(),
        "accounts": BankAccount.query.filter_by(is_active=True).count(),
        "total_balance": money_str(total_balance or 0),
        "transactions": Transaction.query.count(),
        "deposits_total": money_str(deposits or 0),
        "withdrawals_total": money_str(withdrawals or 0),
        "failed_logins_24h": LoginAttempt.query.filter(
            LoginAttempt.success.is_(False),
            LoginAttempt.is_simulation.is_(False),
            LoginAttempt.created_at >= since,
        ).count(),
        "open_alerts": SecurityLog.query.filter(SecurityLog.severity.in_(("warning", "critical"))).count(),
        "recent_transactions": [item.to_dict() for item in recent_transactions],
        "recent_alerts": [item.to_dict() for item in recent_alerts],
    }
