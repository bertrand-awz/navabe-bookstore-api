from unittest.mock import MagicMock, patch

import pytest

from navabe_api import create_app
from navabe_api.config import settings
from navabe_api.infrastructure.mailers import SmtpMailer


def test_smtp_mailer_uses_resend_credentials_and_timeout():
    connection = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = connection

    with patch(
        "navabe_api.infrastructure.mailers.smtplib.SMTP_SSL", return_value=context
    ) as smtp_ssl:
        SmtpMailer(
            "smtp.resend.com",
            465,
            "resend",
            "re_test_key",
            "Navabe Bookstore <no-reply@mail.navabe.bertawz.dev>",
            8,
            "ssl",
        ).send("reader@example.com", "Welcome", "Hello")

    smtp_ssl.assert_called_once_with("smtp.resend.com", 465, timeout=8)
    connection.login.assert_called_once_with("resend", "re_test_key")
    message = connection.send_message.call_args.args[0]
    assert message["From"] == "Navabe Bookstore <no-reply@mail.navabe.bertawz.dev>"
    assert message["To"] == "reader@example.com"


def test_email_enabled_rejects_incomplete_smtp_credentials():
    with pytest.raises(RuntimeError, match="must both be set or both be empty"):
        create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE_BACKEND": "memory",
                "MAIL_ENABLED": True,
                "SMTP_USER": "resend",
                "SMTP_PASSWORD": "",
            }
        )


def test_resend_api_key_is_used_as_smtp_password(monkeypatch):
    monkeypatch.setenv("SMTP_PASSWORD", "")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")

    assert settings()["SMTP_PASSWORD"] == "re_test_key"


def test_smtp_mailer_sends_to_mailhog_without_tls_or_authentication():
    connection = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = connection

    with patch(
        "navabe_api.infrastructure.mailers.smtplib.SMTP", return_value=context
    ) as smtp:
        SmtpMailer(
            "mailhog",
            1025,
            "",
            "",
            "Navabe Bookstore <no-reply@navabe.local>",
            5,
            "none",
        ).send("reader@example.com", "Welcome", "Hello")

    smtp.assert_called_once_with("mailhog", 1025, timeout=5)
    connection.starttls.assert_not_called()
    connection.login.assert_not_called()
    connection.send_message.assert_called_once()


def test_smtp_mailer_adds_html_alternative():
    connection = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = connection

    with patch("navabe_api.infrastructure.mailers.smtplib.SMTP", return_value=context):
        SmtpMailer(
            "mailhog",
            1025,
            "",
            "",
            "Navabe Bookstore <no-reply@navabe.local>",
            5,
            "none",
        ).send("reader@example.com", "Welcome", "Plain version", "<p>HTML version</p>")

    message = connection.send_message.call_args.args[0]
    assert message.get_content_type() == "multipart/alternative"
    assert message.get_body(("plain",)).get_content().strip() == "Plain version"
    assert "<p>HTML version</p>" in message.get_body(("html",)).get_content()
