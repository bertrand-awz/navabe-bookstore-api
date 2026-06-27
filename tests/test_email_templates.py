from navabe_api.application.email_templates import (
    CANVAS_COLOR,
    FOOTER_COLOR,
    FOOTER_TEXT_COLOR,
    LINE_COLOR,
    PAPER_COLOR,
    admin_password_changed_email,
    admin_recovery_email,
    admin_welcome_email,
    customer_password_changed_email,
    customer_recovery_email,
    customer_welcome_email,
)
from navabe_api.domain.models import Admin, User


def test_all_application_emails_render_text_and_html_templates():
    user = User("ALSM0002", "Smith", "Alice", "2 Main Street", "alice@example.com")
    admin = Admin("AD0001", "Admin", "Jane", "admin@example.com")

    emails = (
        customer_welcome_email(user),
        customer_password_changed_email(user),
        customer_recovery_email(user, "tmp-user-password"),
        admin_welcome_email(admin, "tmp-admin-password"),
        admin_recovery_email(admin, "tmp-admin-password"),
        admin_password_changed_email(admin),
    )

    for email in emails:
        assert email.subject
        assert email.text
        assert email.html.startswith("<!doctype html>")
        assert "Navabe" in email.html
        assert "Navabe Bookstore" in email.html
        assert f"background:{CANVAS_COLOR}" in email.html
        assert f"background:{PAPER_COLOR};border-bottom:1px solid {LINE_COLOR}" in email.html
        assert f"background:{FOOTER_COLOR}" in email.html
        assert f"color:{FOOTER_TEXT_COLOR}" in email.html


def test_email_templates_escape_dynamic_html_values():
    user = User("ALSM0002", "Smith", "<Alice>", "2 Main Street", "alice@example.com")

    email = customer_recovery_email(user, "tmp<password>")

    assert "&lt;Alice&gt;" in email.html
    assert "tmp&lt;password&gt;" in email.html
    assert "<Alice>" not in email.html
    assert "tmp<password>" not in email.html
