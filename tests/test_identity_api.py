def test_registers_user_and_opens_session(client, mailer):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Smith",
            "first_name": "Alice",
            "address": "2 Main Street",
            "email": "alice@example.com",
            "password": "password12",
        },
    )

    assert response.status_code == 201
    assert response.json["identifier"] == "ALSM0002"
    assert client.get("/api/v1/auth/me").json["email"] == "alice@example.com"
    assert mailer.messages[0][0] == "alice@example.com"
    assert mailer.messages[0][3]
    assert "Customer identifier" in mailer.messages[0][3]


def test_rejects_invalid_credentials(client):
    response = client.post("/api/v1/auth/login", json={"email": "john@example.com", "password": "wrong"})

    assert response.status_code == 401
    assert response.json["code"] == "invalid_credentials"


def test_changes_password_and_closes_session(user_client):
    response = user_client.patch("/api/v1/auth/password", json={"password": "new-secret"})

    assert response.status_code == 204
    assert user_client.get("/api/v1/auth/me").status_code == 403
    assert user_client.post(
        "/api/v1/auth/login", json={"email": "john@example.com", "password": "new-secret"}
    ).status_code == 200
