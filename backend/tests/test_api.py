from app.services.auth_service import create_user


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def register(client, username="rahul", email="rahul@example.com", password="StrongPass1", full_name="Rahul Sharma"):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
        },
    )


def login(client, username="rahul", password="StrongPass1"):
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    token = response.get_json().get("access_token") if response.is_json else None
    return response, token


def open_account(client, token, holder="Rahul Sharma", balance="100.00", pin="2468"):
    return client.post(
        "/api/accounts",
        headers=auth(token),
        json={"holder_name": holder, "initial_balance": balance, "pin": pin},
    )


def test_health_and_service_index(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.get_json()["database"] == "connected"
    index = client.get("/")
    assert index.status_code == 200
    assert index.get_json()["health"] == "/api/health"


def test_register_login_me_and_logout(client):
    created = register(client)
    assert created.status_code == 201
    body = created.get_json()
    assert "password" not in body["user"]
    assert body["user"]["role"] == "user"

    duplicate = register(client)
    assert duplicate.status_code == 409

    short = register(client, username="mina", email="mina@example.com", password="short")
    assert short.status_code == 400

    failed, _ = login(client, password="WrongPass1")
    assert failed.status_code == 401
    assert failed.get_json()["error"] == "Invalid username or password"

    injected = client.post(
        "/api/auth/login",
        json={"username": "' OR 1=1 --", "password": "whatever"},
    )
    assert injected.status_code == 401

    signed, token = login(client)
    assert signed.status_code == 200
    me = client.get("/api/auth/me", headers=auth(token))
    assert me.status_code == 200
    assert me.get_json()["user"]["username"] == "rahul"

    logged_out = client.post("/api/auth/logout", headers=auth(token))
    assert logged_out.status_code == 200
    rejected = client.get("/api/auth/me", headers=auth(token))
    assert rejected.status_code == 401


def test_private_routes_require_jwt(client):
    assert client.get("/api/accounts").status_code == 401
    assert client.get("/api/accounts/balance").status_code == 401
    assert client.get("/api/transactions/history").status_code == 401
    assert client.get("/api/security/logs").status_code == 401
    assert client.get("/api/admin/dashboard").status_code == 401


def test_accounts_deposits_withdrawals_and_history(client):
    token = register(client).get_json()["access_token"]
    created = open_account(client, token)
    assert created.status_code == 201
    account = created.get_json()["account"]
    assert account["account_number"] == "10000001"
    assert account["balance"] == "100.00"
    assert "pin_hash" not in account

    second = open_account(client, token, holder="Rahul Savings", balance="0")
    assert second.status_code == 201
    assert second.get_json()["account"]["account_number"] == "10000002"

    listed = client.get("/api/accounts", headers=auth(token))
    assert listed.status_code == 200
    assert listed.get_json()["count"] == 2
    assert listed.get_json()["total_balance"] == "100.00"

    balance = client.get("/api/accounts/balance", headers=auth(token))
    assert balance.status_code == 200
    assert balance.get_json()["total_balance"] == "100.00"

    bad_pin = client.post(
        "/api/transactions/deposit",
        headers=auth(token),
        json={"account_id": account["id"], "amount": "25.00", "pin": "0000"},
    )
    assert bad_pin.status_code == 403

    deposited = client.post(
        "/api/transactions/deposit",
        headers=auth(token),
        json={"account_id": account["id"], "amount": "25.50", "pin": "2468"},
    )
    assert deposited.status_code == 201
    assert deposited.get_json()["balance"] == "125.50"

    negative = client.post(
        "/api/transactions/withdraw",
        headers=auth(token),
        json={"account_id": account["id"], "amount": "-5", "pin": "2468"},
    )
    assert negative.status_code == 400

    overdraw = client.post(
        "/api/transactions/withdraw",
        headers=auth(token),
        json={"account_id": account["id"], "amount": "1000", "pin": "2468"},
    )
    assert overdraw.status_code == 400

    withdrawn = client.post(
        "/api/transactions/withdraw",
        headers=auth(token),
        json={"account_id": account["id"], "amount": "25.50", "pin": "2468"},
    )
    assert withdrawn.status_code == 201
    assert withdrawn.get_json()["balance"] == "100.00"

    history = client.get("/api/transactions/history", headers=auth(token))
    payload = history.get_json()
    assert history.status_code == 200
    assert payload["totals"]["count"] == 2
    assert payload["totals"]["deposits"] == "25.50"
    assert payload["totals"]["withdrawals"] == "25.50"
    assert payload["transactions"][0]["txn_type"] == "withdrawal"

    detail = client.get(f"/api/accounts/{account['id']}", headers=auth(token))
    assert detail.status_code == 200
    assert len(detail.get_json()["transactions"]) == 2


def test_account_limit_and_owner_isolation(client):
    owner = register(client).get_json()["access_token"]
    for index in range(10):
        response = open_account(client, owner, holder=f"Account {index}", balance="1.00", pin="1357")
        assert response.status_code == 201
    blocked = open_account(client, owner, holder="Overflow", balance="1.00", pin="1357")
    assert blocked.status_code == 400

    other = register(client, username="meera", email="meera@example.com", full_name="Meera Nair").get_json()
    account_id = client.get("/api/accounts", headers=auth(owner)).get_json()["accounts"][0]["id"]
    assert client.get(f"/api/accounts/{account_id}", headers=auth(other["access_token"])).status_code == 404
    stolen = client.post(
        "/api/transactions/withdraw",
        headers=auth(other["access_token"]),
        json={"account_id": account_id, "amount": "1.00", "pin": "1357"},
    )
    assert stolen.status_code == 404
    balance = client.get("/api/accounts/balance", headers=auth(owner)).get_json()["total_balance"]
    assert balance == "10.00"


def test_change_password(client):
    token = register(client).get_json()["access_token"]
    changed = client.post(
        "/api/auth/change-password",
        headers=auth(token),
        json={"current_password": "StrongPass1", "new_password": "NewerPass99"},
    )
    assert changed.status_code == 200
    old_login, _ = login(client, password="StrongPass1")
    assert old_login.status_code == 401
    new_login, _ = login(client, password="NewerPass99")
    assert new_login.status_code == 200


def test_repeated_failures_are_logged(client):
    register(client)
    for _ in range(5):
        response, _ = login(client, password="WrongPass1")
        assert response.status_code == 401
    _, token = login(client)
    logs = client.get("/api/security/logs", headers=auth(token))
    summary = logs.get_json()["summary"]
    assert summary["failed_attempts"] >= 5
    assert summary["brute_force_alerts"] >= 1
    assert any(item["event_type"] == "repeated_login_failures" for item in logs.get_json()["logs"])


def test_admin_authorization_and_deactivation(client, app):
    token = register(client).get_json()["access_token"]
    account_id = open_account(client, token).get_json()["account"]["id"]
    forbidden = client.get("/api/admin/dashboard", headers=auth(token))
    assert forbidden.status_code == 403
    assert client.get("/api/admin/accounts", headers=auth(token)).status_code == 403

    with app.app_context():
        create_user("adaadmin", "ada@example.com", "Ada Admin", "AdminPass12", role="admin")

    admin_login, admin_token = login(client, "adaadmin", "AdminPass12")
    assert admin_login.status_code == 200
    dashboard = client.get("/api/admin/dashboard", headers=auth(admin_token))
    assert dashboard.status_code == 200
    assert dashboard.get_json()["accounts"] == 1

    listed = client.get("/api/admin/accounts", headers=auth(admin_token))
    assert listed.status_code == 200
    assert listed.get_json()["accounts"][0]["owner"] == "rahul"

    removed = client.delete(f"/api/admin/accounts/{account_id}", headers=auth(admin_token))
    assert removed.status_code == 200
    assert client.get(f"/api/accounts/{account_id}", headers=auth(token)).status_code == 404
    hidden = client.get("/api/admin/accounts", headers=auth(admin_token))
    assert hidden.get_json()["accounts"] == []


def test_simulation_stays_local_and_hides_secrets(client):
    weak = register(client, username="weakuser", email="weak@example.com", password="password", full_name="Weak User")
    weak_token = weak.get_json()["access_token"]
    account_id = open_account(client, weak_token, holder="Weak User").get_json()["account"]["id"]

    missing_ack = client.post(
        "/api/security/brute-force-simulation",
        headers=auth(weak_token),
        json={"account_id": account_id, "attempts": 6, "acknowledge": False},
    )
    assert missing_ack.status_code == 400

    custom = client.post(
        "/api/security/brute-force-simulation",
        headers=auth(weak_token),
        json={"account_id": account_id, "attempts": 6, "acknowledge": True, "wordlist": ["password"]},
    )
    assert custom.status_code == 400

    other = register(client, username="otheruser", email="other@example.com", full_name="Other User")
    other_token = other.get_json()["access_token"]
    denied = client.post(
        "/api/security/brute-force-simulation",
        headers=auth(other_token),
        json={"account_id": account_id, "attempts": 6, "acknowledge": True},
    )
    assert denied.status_code == 404

    result = client.post(
        "/api/security/brute-force-simulation",
        headers=auth(weak_token),
        json={"account_id": account_id, "attempts": 6, "acknowledge": True},
    )
    assert result.status_code == 200
    body = result.get_json()
    assert body["weak_password_detected"] is True
    assert body["successful_guesses"] == 1
    assert "bank123" not in result.get_data(as_text=True)
    assert "abcd" not in result.get_data(as_text=True)
    assert "pin_hash" not in result.get_data(as_text=True)
    assert "password_hash" not in result.get_data(as_text=True)

    strong_token = register(
        client, username="stronguser", email="strong@example.com", password="StrongPass1", full_name="Strong User"
    ).get_json()["access_token"]
    strong_account = open_account(client, strong_token, holder="Strong User").get_json()["account"]["id"]
    clean = client.post(
        "/api/security/brute-force-simulation",
        headers=auth(strong_token),
        json={"account_id": strong_account, "attempts": 6, "acknowledge": True},
    )
    assert clean.status_code == 200
    clean_body = clean.get_json()
    assert clean_body["weak_password_detected"] is False
    assert clean_body["failed_guesses"] == 6
    assert clean_body["repeated_failure_alert"] is True

    logs = client.get("/api/security/logs", headers=auth(strong_token))
    assert logs.status_code == 200
    assert logs.get_json()["summary"]["simulated_attempts"] == 6
    assert any(item["event_type"] == "brute_force_simulation" for item in logs.get_json()["simulations"])


def test_negative_opening_balance_rejected(client):
    token = register(client).get_json()["access_token"]
    response = open_account(client, token, balance="-1")
    assert response.status_code == 400
