from unittest.mock import MagicMock, patch

import pytest

from navabe_api import create_app
from navabe_api.__main__ import main


def test_root_redirects_to_api_documentation(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"] == "/docs"


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
