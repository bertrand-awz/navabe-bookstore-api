from unittest.mock import MagicMock, patch

from navabe_api.__main__ import main


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
