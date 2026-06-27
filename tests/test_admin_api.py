import re


def test_admin_routes_are_protected(client):
    assert client.get("/api/v1/admin/books").status_code == 403


def test_admin_can_upsert_delete_and_search_book(admin_client):
    payload = {
        "isbn": "9780006163831",
        "title": "The One Tree",
        "author": "Stephen Donaldson",
        "category": "Fiction",
        "price": 20,
        "quantity": 3,
    }
    created = admin_client.post("/api/v1/admin/books", json=payload)

    assert created.status_code == 201
    assert created.json["quantity"] == 3
    assert admin_client.get("/api/v1/admin/books?q=Donaldson").json[0]["isbn"] == payload["isbn"]
    assert admin_client.delete(f"/api/v1/admin/books/{payload['isbn']}").status_code == 204


def test_admin_can_find_order_and_get_statistics(user_client, repository):
    order = user_client.post(
        "/api/v1/orders",
        json={
            "transaction_id": "PAYPAL-123",
            "amount": 25,
            "lines": [{"isbn": "9780020199854", "quantity": 1}],
        },
    ).json
    user_client.post("/api/v1/admin/auth/login", json={"identifier": "AD0001", "password": "admin123"})

    assert user_client.get(f"/api/v1/admin/orders/{order['identifier']}").status_code == 200
    stats = user_client.get("/api/v1/admin/statistics/orders").json
    assert stats == {"labels": ["In process"], "values": [1.0]}


def test_manager_must_change_temporary_password_before_access(admin_client, mailer):
    created = admin_client.post(
        "/api/v1/admin/administrators",
        json={"name": "Manager", "first_name": "Root", "email": "root.manager@example.com"},
    )
    assert created.status_code == 201
    assert created.json["must_change_password"] is True

    temporary_password = re.search(r"Temporary password: (.+)", mailer.messages[-1][2]).group(1)

    assert admin_client.post("/api/v1/admin/auth/logout").status_code == 204
    login = admin_client.post(
        "/api/v1/admin/auth/login",
        json={"identifier": created.json["identifier"], "password": temporary_password},
    )
    assert login.status_code == 200
    assert login.json["must_change_password"] is True
    assert admin_client.get("/api/v1/admin/books").json["code"] == "admin_password_change_required"
    assert admin_client.patch(
        "/api/v1/admin/auth/password",
        json={"password": temporary_password},
    ).json["code"] == "password_unchanged"

    changed = admin_client.patch("/api/v1/admin/auth/password", json={"password": "new-manager-password"})

    assert changed.status_code == 204
    assert "management password was changed" in mailer.messages[-1][2]
    assert admin_client.get("/api/v1/admin/books").status_code == 200

    assert admin_client.post("/api/v1/admin/auth/logout").status_code == 204
    assert admin_client.post(
        "/api/v1/admin/auth/recovery",
        json={"identifier": created.json["identifier"]},
    ).status_code == 204
    recovered_password = re.search(r"Temporary password: (.+)", mailer.messages[-1][2]).group(1)

    recovered_login = admin_client.post(
        "/api/v1/admin/auth/login",
        json={"identifier": created.json["identifier"], "password": recovered_password},
    )

    assert recovered_login.status_code == 200
    assert recovered_login.json["must_change_password"] is True
    assert admin_client.get("/api/v1/admin/books").json["code"] == "admin_password_change_required"
