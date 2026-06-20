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

