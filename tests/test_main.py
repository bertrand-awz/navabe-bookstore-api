from unittest.mock import MagicMock, patch

import pytest

from navabe_api import create_app
from navabe_api.__main__ import main


def test_root_redirects_to_api_documentation(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"] == "/docs"


def test_legacy_swagger_path_redirects_to_api_documentation(client):
    response = client.get("/swagger")

    assert response.status_code == 302
    assert response.headers["Location"] == "/docs"


def test_api_documentation_is_available_at_docs(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert b"Navabe Bookstore API" in response.data


def test_production_rejects_placeholder_secret(repository, mailer):
    with pytest.raises(RuntimeError, match="Production SECRET_KEY"):
        create_app(
            {
                "APP_ENV": "production",
                "SECRET_KEY": "replace-with-at-least-32-random-characters",
                "COOKIE_SECURE": True,
                "FRONTEND_ORIGIN": "https://navabe.bertawz.dev",
            },
            repository=repository,
            mailer=mailer,
        )


def test_production_rejects_local_frontend_origin(repository, mailer):
    with pytest.raises(RuntimeError, match="FRONTEND_ORIGIN must not point to localhost"):
        create_app(
            {
                "APP_ENV": "production",
                "SECRET_KEY": "a" * 32,
                "COOKIE_SECURE": True,
                "FRONTEND_ORIGIN": "https://localhost:5173",
                "MYSQL": {"password": "production-password"},
            },
            repository=repository,
            mailer=mailer,
        )


def test_main_loads_dotenv_before_creating_the_app():
    app = MagicMock()

    with (
        patch("navabe_api.__main__.load_dotenv") as load_dotenv,
        patch("navabe_api.__main__.create_app", return_value=app) as create_app,
    ):
        main()

    load_dotenv.assert_called_once_with()
    create_app.assert_called_once_with()
    app.run.assert_called_once_with(host="0.0.0.0", port=5000)
