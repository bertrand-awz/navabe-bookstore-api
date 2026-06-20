def test_customer_creates_order_and_stock_is_reduced(user_client, repository):
    response = user_client.post(
        "/api/v1/orders",
        json={
            "transaction_id": "PAYPAL-123",
            "amount": 50,
            "lines": [{"isbn": "9780020199854", "quantity": 2}],
        },
    )

    assert response.status_code == 201
    assert len(response.json["identifier"]) == 16
    assert repository.books["9780020199854"].quantity == 2


def test_order_rejects_unavailable_stock(user_client):
    response = user_client.post(
        "/api/v1/orders",
        json={
            "transaction_id": "PAYPAL-123",
            "amount": 125,
            "lines": [{"isbn": "9780020199854", "quantity": 5}],
        },
    )

    assert response.status_code == 409
    assert response.json["code"] == "insufficient_stock"


def test_order_rejects_a_total_not_matching_catalog_prices(user_client):
    response = user_client.post(
        "/api/v1/orders",
        json={
            "transaction_id": "PAYPAL-123",
            "amount": 1,
            "lines": [{"isbn": "9780020199854", "quantity": 1}],
        },
    )

    assert response.status_code == 422
    assert response.json["code"] == "invalid_amount"
